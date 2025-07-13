require('dotenv').config();
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');

// Importar middleware
const errorMiddleware = require('./src/presentation/middleware/error-middleware');

// Importar rotas
const authRoutes = require('./src/presentation/routes/auth-routes');
const userRoutes = require('./src/presentation/routes/user-routes');
const quizRoutes = require('./src/presentation/routes/quiz-routes');
const stateRoutes = require('./src/presentation/routes/state-routes');
const politicalEventRoutes = require('./src/presentation/routes/political-event-routes');

// Importar utils
const { testConnection } = require('./src/infrastructure/database/supabase-client');

// [CORRIGIDO] Importar job econômica e constantes
const EconomicUpdateJob = require('./src/infrastructure/jobs/economic-update-job');
const { ECONOMIC_CONSTANTS } = require('./src/shared/constants/economic-constants');

const app = express();
const PORT = process.env.PORT || 3000;

// Instância da job econômica
let economicJob = null;

// Configuração de Rate Limiting
const limiter = rateLimit({
    windowMs: parseInt(process.env.RATE_LIMIT_WINDOW_MS) || 15 * 60 * 1000, // 15 minutos
    max: parseInt(process.env.RATE_LIMIT_MAX_REQUESTS) || 100, // limite de 100 requests por IP
    message: {
        success: false,
        message: 'Muitas tentativas. Tente novamente em alguns minutos.',
        timestamp: new Date().toISOString()
    }
});

// Middlewares de segurança
app.use(helmet());
app.use(cors({
    origin: process.env.FRONTEND_URL || 'http://localhost:3000',
    credentials: true
}));
app.use(limiter);

// Middleware para parsing JSON
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Middleware para logs
app.use((req, res, next) => {
    console.log(`${new Date().toISOString()} - ${req.method} ${req.path} - IP: ${req.ip}`);
    next();
});

// Health check
app.get('/health', (req, res) => {
    res.json({
        success: true,
        message: 'SimNations Backend está funcionando!',
        timestamp: new Date().toISOString(),
        environment: process.env.NODE_ENV || 'development',
        economic_job_status: economicJob ? economicJob.getStatus() : 'not_initialized'
    });
});

// Rota para status da job econômica
app.get('/admin/economic-job/status', (req, res) => {
    if (!economicJob) {
        return res.status(503).json({
            success: false,
            message: 'Job econômica não inicializada'
        });
    }

    res.json({
        success: true,
        data: economicJob.getStatus(),
        timestamp: new Date().toISOString()
    });
});

// Rota para execução manual da job (apenas em desenvolvimento)
if (process.env.NODE_ENV === 'development') {
    app.post('/admin/economic-job/execute', async (req, res) => {
        if (!economicJob) {
            return res.status(503).json({
                success: false,
                message: 'Job econômica não inicializada'
            });
        }

        try {
            const result = await economicJob.executeManual();
            res.json({
                success: true,
                data: result,
                timestamp: new Date().toISOString()
            });
        } catch (error) {
            res.status(500).json({
                success: false,
                message: 'Erro ao executar job manualmente',
                error: error.message
            });
        }
    });
}

// Rotas da API
app.use('/api/auth', authRoutes);
app.use('/api/user', userRoutes);
app.use('/api/quiz', quizRoutes);
app.use('/api/state', stateRoutes);
app.use('/api/events', politicalEventRoutes);

// Middleware de tratamento de erros
app.use(errorMiddleware);

// Rota para 404
app.use('*', (req, res) => {
    res.status(404).json({
        success: false,
        message: 'Rota não encontrada',
        timestamp: new Date().toISOString()
    });
});

// Inicializar servidor
async function startServer() {
    try {
        // Testar conexão com banco
        const isConnected = await testConnection();
        if (!isConnected) {
            console.error('❌ Falha na conexão com o banco de dados');
            process.exit(1);
        }

        // Inicializar job econômica
        if (process.env.NODE_ENV !== 'test') { // Não executar em testes
            economicJob = new EconomicUpdateJob();
            economicJob.start();
        }

        // Iniciar servidor
        app.listen(PORT, () => {
            console.log(`🚀 Servidor rodando na porta ${PORT}`);
            console.log(`🌟 Environment: ${process.env.NODE_ENV || 'development'}`);
            console.log(`📊 Health check: http://localhost:${PORT}/health`);
            
            if (economicJob) {
                console.log(`🏛️ Job econômica ativa: ${ECONOMIC_CONSTANTS.JOB_SCHEDULE}`);
                if (process.env.NODE_ENV === 'development') {
                    console.log(`🔧 Execução manual: POST http://localhost:${PORT}/admin/economic-job/execute`);
                }
            }
        });
    } catch (error) {
        console.error('❌ Erro ao iniciar servidor:', error);
        process.exit(1);
    }
}

// Tratamento de erros não capturados
process.on('uncaughtException', (error) => {
    console.error('❌ Uncaught Exception:', error);
    process.exit(1);
});

process.on('unhandledRejection', (reason, promise) => {
    console.error('❌ Unhandled Rejection at:', promise, 'reason:', reason);
    process.exit(1);
});

// Graceful shutdown
process.on('SIGTERM', () => {
    console.log('🔄 SIGTERM recebido, encerrando servidor...');
    if (economicJob) {
        economicJob.stop();
    }
    process.exit(0);
});

process.on('SIGINT', () => {
    console.log('🔄 SIGINT recebido, encerrando servidor...');
    if (economicJob) {
        economicJob.stop();
    }
    process.exit(0);
});

// Iniciar aplicação
startServer();