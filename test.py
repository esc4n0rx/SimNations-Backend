import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional
import sys

class Colors:
    """Cores para output no terminal"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class SimNationsCompleteTester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.access_token = None
        self.current_user = None
        self.test_results = []
        self.current_email = None
        
    def print_header(self, text: str):
        """Imprime cabeçalho colorido"""
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}")
        print(f"🚀 {text}")
        print(f"{'='*80}{Colors.ENDC}")
    
    def print_step(self, step: str, description: str):
        """Imprime passo do teste"""
        print(f"\n{Colors.OKBLUE}{Colors.BOLD}[PASSO {step}]{Colors.ENDC} {description}")
        print(f"{Colors.OKCYAN}{'─'*60}{Colors.ENDC}")
    
    def print_request(self, method: str, url: str, data: Any = None):
        """Imprime detalhes da requisição"""
        print(f"{Colors.WARNING}📤 {method} {url}{Colors.ENDC}")
        if data:
            print(f"📋 Dados enviados:")
            print(f"   {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    def print_response(self, response: requests.Response):
        """Imprime resposta detalhada"""
        status_color = Colors.OKGREEN if response.status_code < 400 else Colors.FAIL
        print(f"{status_color}📥 Status: {response.status_code}{Colors.ENDC}")
        
        try:
            response_data = response.json()
            print(f"📋 Resposta:")
            print(f"   {json.dumps(response_data, indent=2, ensure_ascii=False)}")
        except:
            print(f"📋 Resposta (texto): {response.text}")
    
    def print_success(self, message: str):
        """Imprime mensagem de sucesso"""
        print(f"{Colors.OKGREEN}✅ {message}{Colors.ENDC}")
    
    def print_error(self, message: str):
        """Imprime mensagem de erro"""
        print(f"{Colors.FAIL}❌ {message}{Colors.ENDC}")
    
    def print_info(self, message: str):
        """Imprime informação"""
        print(f"{Colors.OKCYAN}ℹ️  {message}{Colors.ENDC}")
    
    def wait_for_input(self, message: str = "Pressione ENTER para continuar..."):
        """Aguarda input do usuário"""
        print(f"\n{Colors.WARNING}⏸️  {message}{Colors.ENDC}")
        input()
    
    def test_with_details(self, test_name: str, test_func, *args, **kwargs):
        """Executa teste com logs detalhados"""
        print(f"\n{Colors.BOLD}🧪 Executando: {test_name}{Colors.ENDC}")
        start_time = time.time()
        
        try:
            result = test_func(*args, **kwargs)
            end_time = time.time()
            duration = round(end_time - start_time, 2)
            
            if result:
                self.print_success(f"{test_name} - Concluído em {duration}s")
                self.test_results.append((test_name, "✅ PASSOU", duration))
            else:
                self.print_error(f"{test_name} - Falhou em {duration}s")
                self.test_results.append((test_name, "❌ FALHOU", duration))
            
            return result
        except Exception as e:
            end_time = time.time()
            duration = round(end_time - start_time, 2)
            self.print_error(f"{test_name} - Erro: {str(e)} ({duration}s)")
            self.test_results.append((test_name, f"❌ ERRO: {str(e)}", duration))
            return False
    
    def test_health_check(self):
        """Teste 1: Health Check"""
        self.print_step("1", "Health Check - Verificando se a API está funcionando")
        
        url = f"{self.base_url}/health"
        self.print_request("GET", url)
        
        response = self.session.get(url)
        self.print_response(response)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "healthy":
                self.print_success("API está funcionando corretamente!")
                return True
        
        self.print_error("API não está respondendo corretamente")
        return False
    
    def test_register(self):
        """Teste 2: Registro de usuário"""
        self.print_step("2", "Registro de Usuário - Criando nova conta")
        
        timestamp = int(time.time())
        self.current_email = f"teste_{timestamp}@simnations.com"
        
        data = {
            "name": f"Usuário Teste {timestamp}",
            "email": self.current_email,
            "birth_date": "1990-05-15",
            "password": "senhaSegura123"
        }
        
        url = f"{self.base_url}/auth/register"
        self.print_request("POST", url, data)
        
        response = self.session.post(url, json=data)
        self.print_response(response)
        
        if response.status_code == 201:
            self.current_user = response.json()
            self.print_success(f"Usuário registrado com ID: {self.current_user['id']}")
            self.print_info(f"Email: {self.current_user['email']}")
            self.print_info(f"Nome: {self.current_user['name']}")
            return True
        
        self.print_error("Falha no registro do usuário")
        return False
    
    def test_login(self):
        """Teste 3: Login"""
        self.print_step("3", "Login - Autenticando usuário")
        
        if not self.current_email:
            self.print_error("Não há email disponível para login")
            return False
        
        data = {
            "email": self.current_email,
            "password": "senhaSegura123"
        }
        
        url = f"{self.base_url}/auth/login"
        self.print_request("POST", url, data)
        
        response = self.session.post(url, json=data)
        self.print_response(response)
        
        if response.status_code == 200:
            token_data = response.json()
            self.access_token = token_data["access_token"]
            self.session.headers.update({"Authorization": f"Bearer {self.access_token}"})
            
            self.print_success("Login realizado com sucesso!")
            self.print_info(f"Token obtido: {self.access_token[:50]}...")
            return True
        
        self.print_error("Falha no login")
        return False
    
    def test_get_current_user(self):
        """Teste 4: Obter usuário atual"""
        self.print_step("4", "Usuário Atual - Verificando dados do usuário logado")
        
        url = f"{self.base_url}/auth/me"
        self.print_request("GET", url)
        
        response = self.session.get(url)
        self.print_response(response)
        
        if response.status_code == 200:
            user_data = response.json()
            self.print_success("Dados do usuário obtidos com sucesso!")
            self.print_info(f"ID: {user_data['id']}")
            self.print_info(f"Nome: {user_data['name']}")
            self.print_info(f"Email: {user_data['email']}")
            self.print_info(f"Ativo: {user_data['is_active']}")
            return True
        
        self.print_error("Falha ao obter dados do usuário")
        return False
    
    def test_user_profile_complete(self):
        """Teste 5: Perfil completo do usuário"""
        self.print_step("5", "Perfil Completo - Verificando status completo do usuário")
        
        url = f"{self.base_url}/users/profile/complete"
        self.print_request("GET", url)
        
        response = self.session.get(url)
        self.print_response(response)
        
        if response.status_code == 200:
            profile = response.json()
            self.print_success("Perfil completo obtido!")
            self.print_info(f"Quiz completo: {profile['quiz_completed']}")
            self.print_info(f"Tem estado: {profile['has_state']}")
            return True
        
        self.print_error("Falha ao obter perfil completo")
        return False
    
    def test_quiz_questions(self):
        """Teste 6: Obter questões do quiz"""
        self.print_step("6", "Questões do Quiz - Carregando perguntas da personalidade")
        
        url = f"{self.base_url}/quiz/questions"
        self.print_request("GET", url)
        
        response = self.session.get(url)
        self.print_response(response)
        
        if response.status_code == 200:
            questions = response.json()
            self.print_success(f"Carregadas {len(questions)} questões do quiz!")
            
            # Mostra algumas questões como exemplo
            for i, question in enumerate(questions[:3]):
                self.print_info(f"Q{question['id']}: {question['question']}")
                self.print_info(f"Categoria: {question['category']}")
            
            if len(questions) > 3:
                self.print_info(f"... e mais {len(questions) - 3} questões")
            
            return True
        
        self.print_error("Falha ao carregar questões do quiz")
        return False
    
    def test_quiz_submit(self):
        """Teste 7: Submeter respostas do quiz"""
        self.print_step("7", "Submeter Quiz - Enviando respostas da personalidade")
        
        # Gera respostas automáticas variadas
        answers = []
        categories = ["racionalidade", "conservadorismo", "audacia", "autoridade", "coletivismo", "influencia"]
        
        question_id = 1
        for cat_index, category in enumerate(categories):
            for q in range(3):  # 3 perguntas por categoria
                # Varia as respostas por categoria para ter personalidade diversa
                base_value = 2 + (cat_index % 4)  # Valores entre 2-5
                variation = (question_id % 3) - 1  # -1, 0, 1
                answer_value = max(1, min(5, base_value + variation))
                
                answers.append({
                    "question_id": question_id,
                    "category": category,
                    "answer_value": answer_value
                })
                question_id += 1
        
        data = {"answers": answers}
        
        url = f"{self.base_url}/quiz/submit"
        self.print_request("POST", url, {"answers": f"[{len(answers)} respostas]"})
        
        response = self.session.post(url, json=data)
        self.print_response(response)
        
        if response.status_code == 200:
            result = response.json()
            self.print_success("Quiz submetido com sucesso!")
            
            if "quiz_result" in result:
                traits = result["quiz_result"]
                self.print_info("📊 Personalidade calculada:")
                for trait, value in traits.items():
                    if trait != "reroll_count":
                        self.print_info(f"   {trait.capitalize()}: {value}")
            
            if result.get("state_assigned"):
                state = result.get("assigned_state", {})
                self.print_success(f"🏛️ Estado atribuído automaticamente!")
                self.print_info(f"Estado: {state.get('name')}")
                self.print_info(f"País: {state.get('country_name')}")
            
            return True
        
        self.print_error("Falha ao submeter quiz")
        return False
    
    def test_my_state(self):
        """Teste 8: Verificar meu estado"""
        self.print_step("8", "Meu Estado - Verificando estado atribuído")
        
        url = f"{self.base_url}/states/my-state"
        self.print_request("GET", url)
        
        response = self.session.get(url)
        self.print_response(response)
        
        if response.status_code == 200:
            state = response.json()
            if state:
                self.print_success("Estado encontrado!")
                self.print_info(f"🏛️ Estado: {state['name']}")
                self.print_info(f"🌍 País: {state['country_name']}")
                self.print_info(f"👤 Gerenciado por: {state['manager_name']}")
                self.print_info(f"📊 Características:")
                self.print_info(f"   Racionalidade: {state['racionalidade']}")
                self.print_info(f"   Conservadorismo: {state['conservadorismo']}")
                self.print_info(f"   Audácia: {state['audacia']}")
                self.print_info(f"   Autoridade: {state['autoridade']}")
                self.print_info(f"   Coletivismo: {state['coletivismo']}")
                self.print_info(f"   Influência: {state['influencia']}")
            else:
                self.print_info("Nenhum estado atribuído ainda")
            return True
        
        self.print_error("Falha ao verificar estado")
        return False
    
    def test_compatible_states(self):
        """Teste 9: Estados compatíveis"""
        self.print_step("9", "Estados Compatíveis - Verificando matches da personalidade")
        
        url = f"{self.base_url}/states/compatible?limit=5"
        self.print_request("GET", url)
        
        response = self.session.get(url)
        self.print_response(response)
        
        if response.status_code == 200:
            compatible_states = response.json()
            self.print_success(f"Encontrados {len(compatible_states)} estados compatíveis!")
            
            for i, match in enumerate(compatible_states[:3]):
                state = match["state"]
                score = match["compatibility_score"]
                self.print_info(f"#{i+1} {state['name']}, {state['country_name']} - {score}% compatível")
            
            return True
        
        self.print_error("Falha ao obter estados compatíveis")
        return False
    
    def test_user_statistics(self):
        """Teste 10: Estatísticas do usuário"""
        self.print_step("10", "Estatísticas - Verificando progresso do usuário")
        
        url = f"{self.base_url}/users/statistics"
        self.print_request("GET", url)
        
        response = self.session.get(url)
        self.print_response(response)
        
        if response.status_code == 200:
            stats = response.json()
            self.print_success("Estatísticas obtidas!")
            self.print_info(f"📅 Dias ativo: {stats['days_active']}")
            self.print_info(f"✅ Quiz completo: {stats['quiz_completed']}")
            self.print_info(f"🏛️ Tem estado: {stats['has_state']}")
            self.print_info(f"🔄 Rerolls usados: {stats['rerolls_used']}")
            self.print_info(f"🎲 Rerolls restantes: {stats['rerolls_remaining']}")
            return True
        
        self.print_error("Falha ao obter estatísticas")
        return False
    
    def test_reroll_state(self):
        """Teste 11: Reroll do estado (se possível)"""
        self.print_step("11", "Reroll Estado - Testando nova atribuição de estado")
        
        url = f"{self.base_url}/states/reroll"
        self.print_request("POST", url)
        
        response = self.session.post(url)
        self.print_response(response)
        
        if response.status_code == 200:
            result = response.json()
            self.print_success("Reroll realizado com sucesso!")
            state = result["assigned_state"]
            self.print_info(f"🏛️ Novo estado: {state['name']}")
            self.print_info(f"🌍 País: {state['country_name']}")
            self.print_info(f"🎲 Rerolls restantes: {result['rerolls_remaining']}")
            return True
        elif response.status_code == 400:
            error_data = response.json()
            self.print_info(f"Reroll não disponível: {error_data.get('detail')}")
            return True  # Não é erro, apenas não tem rerolls disponíveis
        
        self.print_error("Falha no reroll")
        return False
    
    def test_state_statistics(self):
        """Teste 12: Estatísticas dos estados"""
        self.print_step("12", "Estatísticas Gerais - Verificando status do servidor")
        
        url = f"{self.base_url}/states/statistics"
        self.print_request("GET", url)
        
        response = self.session.get(url)
        self.print_response(response)
        
        if response.status_code == 200:
            stats = response.json()
            self.print_success("Estatísticas gerais obtidas!")
            self.print_info(f"🌍 Total de estados: {stats['total_states']}")
            self.print_info(f"🏛️ Estados ocupados: {stats['occupied_states']}")
            self.print_info(f"🆓 Estados disponíveis: {stats['available_states']}")
            
            if stats['total_states'] > 0:
                ocupacao = (stats['occupied_states'] / stats['total_states']) * 100
                self.print_info(f"📊 Taxa de ocupação: {ocupacao:.2f}%")
            
            return True
        
        self.print_error("Falha ao obter estatísticas gerais")
        return False
    
    def show_final_report(self):
        """Mostra relatório final dos testes"""
        self.print_header("RELATÓRIO FINAL DOS TESTES")
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if "✅" in r[1]])
        failed_tests = total_tests - passed_tests
        
        print(f"\n{Colors.BOLD}📊 RESUMO:{Colors.ENDC}")
        print(f"   Total de testes: {total_tests}")
        print(f"   {Colors.OKGREEN}✅ Passou: {passed_tests}{Colors.ENDC}")
        print(f"   {Colors.FAIL}❌ Falhou: {failed_tests}{Colors.ENDC}")
        
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        color = Colors.OKGREEN if success_rate >= 80 else Colors.WARNING if success_rate >= 60 else Colors.FAIL
        print(f"   {color}📈 Taxa de sucesso: {success_rate:.1f}%{Colors.ENDC}")
        
        print(f"\n{Colors.BOLD}📋 DETALHES:{Colors.ENDC}")
        print(f"{'Teste':<40} {'Status':<20} {'Tempo'}")
        print("─" * 70)
        
        for test_name, status, duration in self.test_results:
            print(f"{test_name:<40} {status:<20} {duration}s")
        
        if self.current_user:
            print(f"\n{Colors.BOLD}👤 USUÁRIO CRIADO:{Colors.ENDC}")
            print(f"   Email: {self.current_email}")
            print(f"   ID: {self.current_user.get('id')}")
            print(f"   Nome: {self.current_user.get('name')}")
        
        print(f"\n{Colors.OKGREEN}🎉 Testes concluídos! Obrigado por usar o SimNations API Tester.{Colors.ENDC}")
    
    def run_all_tests(self):
        """Executa todos os testes com controle manual"""
        self.print_header("TESTE COMPLETO DO SIMNATIONS API")
        print(f"{Colors.OKCYAN}Este teste irá verificar todos os endpoints e fluxos da API.{Colors.ENDC}")
        print(f"{Colors.WARNING}Você pode controlar o ritmo pressionando ENTER entre os testes.{Colors.ENDC}")
        
        self.wait_for_input("Pressione ENTER para iniciar os testes...")
        
        # Lista de testes
        tests = [
            ("Health Check", self.test_health_check),
            ("Registro de Usuário", self.test_register),
            ("Login", self.test_login),
            ("Usuário Atual", self.test_get_current_user),
            ("Perfil Completo", self.test_user_profile_complete),
            ("Questões do Quiz", self.test_quiz_questions),
            ("Submeter Quiz", self.test_quiz_submit),
            ("Meu Estado", self.test_my_state),
            ("Estados Compatíveis", self.test_compatible_states),
            ("Estatísticas do Usuário", self.test_user_statistics),
            ("Reroll Estado", self.test_reroll_state),
            ("Estatísticas Gerais", self.test_state_statistics),
        ]
        
        for i, (test_name, test_func) in enumerate(tests, 1):
            success = self.test_with_details(test_name, test_func)
            
            if i < len(tests):  # Não espera após o último teste
                self.wait_for_input(f"[{i}/{len(tests)}] Teste concluído. Continuar para o próximo?")
        
        self.show_final_report()

def main():
    """Função principal"""
    print(f"{Colors.HEADER}{Colors.BOLD}")
    print("╔══════════════════════════════════════════════════════════════════════════════╗")
    print("║                        SIMNATIONS API TESTER v2.0                           ║")
    print("║                     Teste Completo com Logs Visuais                         ║")
    print("╚══════════════════════════════════════════════════════════════════════════════╝")
    print(f"{Colors.ENDC}")
    
    # Verificar se API está rodando
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code != 200:
            raise Exception("API não está respondendo corretamente")
    except Exception as e:
        print(f"{Colors.FAIL}❌ Erro: Não foi possível conectar à API em http://localhost:8000{Colors.ENDC}")
        print(f"   Certifique-se de que o servidor está rodando com: python main.py")
        print(f"   Erro: {e}")
        sys.exit(1)
    
    # Executar testes
    tester = SimNationsCompleteTester()
    
    try:
        tester.run_all_tests()
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}⚠️  Testes interrompidos pelo usuário.{Colors.ENDC}")
        tester.show_final_report()
    except Exception as e:
        print(f"\n{Colors.FAIL}❌ Erro inesperado: {e}{Colors.ENDC}")
        tester.show_final_report()

if __name__ == "__main__":
    main()