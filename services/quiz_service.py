from typing import List, Dict
from sqlalchemy.orm import Session
from models.quiz import QuizResult
from models.user import User
from schemas.quiz_schema import QuizSubmission, QuizQuestion, QuizCategory

class QuizService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_quiz_questions(self) -> List[QuizQuestion]:
        """Get all quiz questions"""
        questions = [
            # Racionalidade
            QuizQuestion(
                id=1,
                category=QuizCategory.RACIONALIDADE,
                question="Ao tomar decisões importantes, você prefere:",
                options=["Analisar dados e estatísticas", "Seguir sua intuição", "Consultar especialistas", "Considerar experiências passadas", "Buscar opiniões de outros"]
            ),
            QuizQuestion(
                id=2,
                category=QuizCategory.RACIONALIDADE,
                question="Diante de um problema complexo, sua primeira reação é:",
                options=["Dividir em partes menores", "Buscar soluções criativas", "Procurar exemplos similares", "Pedir ajuda", "Tentar várias abordagens"]
            ),
            QuizQuestion(
                id=3,
                category=QuizCategory.RACIONALIDADE,
                question="Você acredita que as melhores decisões são baseadas em:",
                options=["Lógica e razão", "Emoções e sentimentos", "Experiência prática", "Consenso do grupo", "Tradição e costume"]
            ),
            
            # Conservadorismo
            QuizQuestion(
                id=4,
                category=QuizCategory.CONSERVADORISMO,
                question="Sua atitude em relação a mudanças é:",
                options=["Muito cautelosa", "Moderadamente cautelosa", "Neutra", "Moderadamente aberta", "Muito aberta"]
            ),
            QuizQuestion(
                id=5,
                category=QuizCategory.CONSERVADORISMO,
                question="Você valoriza mais:",
                options=["Tradições estabelecidas", "Inovação e progresso", "Equilíbrio entre ambos", "Adaptação às circunstâncias", "Experimentação constante"]
            ),
            QuizQuestion(
                id=6,
                category=QuizCategory.CONSERVADORISMO,
                question="Ao formar sua opinião sobre questões sociais, você considera:",
                options=["Valores tradicionais", "Tendências modernas", "Evidências científicas", "Opinião popular", "Experiência pessoal"]
            ),
            
            # Audácia
            QuizQuestion(
                id=7,
                category=QuizCategory.AUDACIA,
                question="Diante de uma oportunidade arriscada mas promissora, você:",
                options=["Aceita imediatamente", "Aceita após análise", "Hesita bastante", "Geralmente recusa", "Sempre recusa"]
            ),
            QuizQuestion(
                id=8,
                category=QuizCategory.AUDACIA,
                question="Sua tolerância a riscos é:",
                options=["Muito alta", "Alta", "Moderada", "Baixa", "Muito baixa"]
            ),
            QuizQuestion(
                id=9,
                category=QuizCategory.AUDACIA,
                question="Você prefere:",
                options=["Grandes apostas, grandes ganhos", "Riscos calculados", "Segurança moderada", "Máxima segurança", "Evitar qualquer risco"]
            ),
            
            # Autoridade
            QuizQuestion(
                id=10,
                category=QuizCategory.AUTORIDADE,
                question="Em um grupo, você naturalmente:",
                options=["Assume a liderança", "Oferece sugestões", "Participa ativamente", "Segue as diretrizes", "Observa silenciosamente"]
            ),
            QuizQuestion(
                id=11,
                category=QuizCategory.AUTORIDADE,
                question="Sua atitude em relação a hierarquias é:",
                options=["Muito respeitosa", "Respeitosa", "Neutra", "Questionadora", "Desafiadora"]
            ),
            QuizQuestion(
                id=12,
                category=QuizCategory.AUTORIDADE,
                question="Você acredita que a autoridade deve ser:",
                options=["Absoluta", "Forte mas questionável", "Equilibrada", "Limitada", "Mínima"]
            ),
            
            # Coletivismo
            QuizQuestion(
                id=13,
                category=QuizCategory.COLETIVISMO,
                question="Ao tomar decisões, você prioriza:",
                options=["Bem-estar do grupo", "Equilíbrio grupo-individual", "Suas próprias necessidades", "Eficiência", "Tradições"]
            ),
            QuizQuestion(
                id=14,
                category=QuizCategory.COLETIVISMO,
                question="Você acredita que o sucesso individual:",
                options=["Deve servir ao coletivo", "Deve ser equilibrado", "É mais importante", "Depende da situação", "É irrelevante"]
            ),
            QuizQuestion(
                id=15,
                category=QuizCategory.COLETIVISMO,
                question="Sua preferência de trabalho é:",
                options=["Sempre em equipe", "Preferencialmente em equipe", "Tanto faz", "Preferencialmente individual", "Sempre individual"]
            ),
            
            # Influência
            QuizQuestion(
                id=16,
                category=QuizCategory.INFLUENCIA,
                question="Você gosta de:",
                options=["Liderar e influenciar", "Persuadir ocasionalmente", "Participar ativamente", "Seguir e apoiar", "Observar discretamente"]
            ),
            QuizQuestion(
                id=17,
                category=QuizCategory.INFLUENCIA,
                question="Sua habilidade de convencer outros é:",
                options=["Muito alta", "Alta", "Moderada", "Baixa", "Muito baixa"]
            ),
            QuizQuestion(
                id=18,
                category=QuizCategory.INFLUENCIA,
                question="Você prefere:",
                options=["Ser o centro das atenções", "Ter visibilidade moderada", "Manter perfil neutro", "Ser discreto", "Passar despercebido"]
            )
        ]
        
        return questions
    
    def calculate_personality_traits(self, quiz_submission: QuizSubmission) -> Dict[str, float]:
        """Calculate personality traits from quiz answers"""
        traits = {
            'racionalidade': 0.0,
            'conservadorismo': 0.0,
            'audacia': 0.0,
            'autoridade': 0.0,
            'coletivismo': 0.0,
            'influencia': 0.0
        }
        
        # Group answers by category
        category_answers = {}
        for answer in quiz_submission.answers:
            category = answer.category.value
            if category not in category_answers:
                category_answers[category] = []
            category_answers[category].append(answer.answer_value)
        
        # Calculate average for each trait (scale 1-5 to 0-10)
        for category, answers in category_answers.items():
            if len(answers) == 3:  # Should have exactly 3 answers per category
                average = sum(answers) / len(answers)
                traits[category] = round((average - 1) * 2.5, 1)  # Convert 1-5 to 0-10
        
        return traits
    
    def save_quiz_result(self, user: User, quiz_submission: QuizSubmission, auto_assign_state: bool = True) -> QuizResult:
        """Save quiz result for user and optionally auto-assign state"""
        traits = self.calculate_personality_traits(quiz_submission)
        
        # Check if user already has a quiz result
        existing_result = self.db.query(QuizResult).filter(QuizResult.user_id == user.id).first()
        
        if existing_result:
            # Update existing result
            existing_result.racionalidade = traits['racionalidade']
            existing_result.conservadorismo = traits['conservadorismo']
            existing_result.audacia = traits['audacia']
            existing_result.autoridade = traits['autoridade']
            existing_result.coletivismo = traits['coletivismo']
            existing_result.influencia = traits['influencia']
            existing_result.answers = [answer.dict() for answer in quiz_submission.answers]
            quiz_result = existing_result
        else:
            # Create new result
            quiz_result = QuizResult(
                user_id=user.id,
                racionalidade=traits['racionalidade'],
                conservadorismo=traits['conservadorismo'],
                audacia=traits['audacia'],
                autoridade=traits['autoridade'],
                coletivismo=traits['coletivismo'],
                influencia=traits['influencia'],
                answers=[answer.dict() for answer in quiz_submission.answers]
            )
            self.db.add(quiz_result)
        
        self.db.commit()
        self.db.refresh(quiz_result)
        
        # Auto-assign state if requested and user doesn't have one
        if auto_assign_state:
            from models.state import State
            existing_state = self.db.query(State).filter(State.manager_id == user.id).first()
            
            if not existing_state:
                try:
                    from services.matching_service import MatchingService
                    matching_service = MatchingService(self.db)
                    state = matching_service.get_random_compatible_state(quiz_result)
                    matching_service.assign_state_to_user(state, user.id)
                    print(f"Estado '{state.name}' automaticamente atribuído ao usuário '{user.name}'")
                except Exception as e:
                    print(f"Erro ao atribuir estado automaticamente: {e}")
        
        return quiz_result
    
    def get_user_quiz_result(self, user: User) -> QuizResult:
        """Get user's quiz result"""
        return self.db.query(QuizResult).filter(QuizResult.user_id == user.id).first()