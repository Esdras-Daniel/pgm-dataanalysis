from typing import Callable, Dict, List, Any, Union
from enum import Enum
import pprint

class ClassLabel(Enum):
    ADMINISTRATIVA = "Administrativa"
    FISCAL = "Fiscal"
    JUDICIAL = "Judicial"
    MEIO_AMBIENTE = 'Meio Ambiente'
    PATRIMONIAL = 'Patrimonial'
    CONTABILIDADE = 'Contabilidade'
    CARTORIO = 'Cartório'
    SAUDE = 'Saúde'
    PRDA = 'PRDA'

class Rule:
    def __init__(self, funcao: Callable[[Dict], bool], nome: str, consequente: ClassLabel):
        self.funcao = funcao
        self.nome = nome
        self.consequente = consequente
        self.qtd_calls = 0
        self.qtd_positive_calls = 0

    def avaliar(self, entrada: Dict, train_mode: bool=False) -> bool:
        resultado = self.funcao(entrada)
        if train_mode:
            if resultado:
                self.qtd_calls += 1
                if entrada.get('setorDestino') == self.consequente.value:
                    self.qtd_positive_calls += 1
        return resultado

    def calcular_precisao(self) -> float:
        return self.qtd_positive_calls / self.qtd_calls if self.qtd_calls > 0 else 0.0

    def calcular_suporte(self) -> int:
        return self.qtd_calls

class RuleBasedClassifier:
    def __init__(self):
        self.rules: List[Rule] = []
        self.train_data: List[Dict] = []

    def add_rule(self, rule: Rule):
        self.rules.append(rule)

    def predict(self, data: Union[Dict, List[Dict]]) -> Union[Dict[str, float], List[Dict[str, float]]]:
        if isinstance(data, dict):
            return self._classify_with_confidence(data)
        elif isinstance(data, list):
            return [self._classify_with_confidence(item) for item in data]
        else:
            raise ValueError("Entrada deve ser um dicionário ou uma lista de dicionários.")

    def _classify_with_confidence(self, data: Dict) -> Dict[str, float]:
        class_scores = {}
        total_weight = 0
        
        for rule in self.rules:
            if rule.avaliar(data):
                precisao = rule.calcular_precisao()
                suporte = rule.calcular_suporte()
                peso = precisao * suporte
                
                if rule.consequente.value not in class_scores:
                    class_scores[rule.consequente.value] = 0
                class_scores[rule.consequente.value] += peso
                total_weight += peso

        if total_weight == 0:
            return {"Indefinido": 0.0}
        
        return {classe: (pontuacao / total_weight) * 100 for classe, pontuacao in class_scores.items()}

    def train(self, data: List[Dict]):
        self.train_data = data #[dict(zip(data.keys(), valores)) for valores in zip(*data.values())]
        for item in self.train_data:
            for rule in self.rules:
                rule.avaliar(item, train_mode=True)


    def calcular_metricas(self) -> Dict[str, Dict[str, float]]:
        return {
            rule.nome: {
                "precisao": rule.calcular_precisao(),
                "suporte": rule.calcular_suporte(),
            } 
            for rule in self.rules
        }

def main():
    # Importando os dados
    import pandas as pd
    import os
    from dotenv import load_dotenv
    load_dotenv()

    N_SAMPLES = 5000

    data = pd.read_csv(os.path.join(os.environ['PATH_DATA_PROCESSED'], 'pgm-dataset-processado.csv'))
    data_sample = data.sample(n=N_SAMPLES, replace=False, random_state=42).drop(columns=(['teorTexto', 'documentos', 'anexos']))
    data_sample = data_sample.to_dict(orient='list')
    
    # Formata data_sample para uma lista de dicionários do formato {coluna:valor}
    data_sample = [dict(zip(data_sample.keys(), valores)) for valores in zip(*data_sample.values())]
    print(data_sample[:2])
    # Separando em dados de treinamento e teste
    train_size = 0.7
    X_train = data_sample[:int(N_SAMPLES*train_size)]
    X_test = data_sample[int(N_SAMPLES*train_size):]
    
    # Funções para a Fiscal
    def fiscal1(data):
        return ('5952' in data['assuntos'])
    def fiscal2(data):
        return ('10536' in data['assuntos'])    
    def fiscal3(data):
        return ('5952' in data['assuntos'] and '10536' in data['assuntos'])
    def fiscal4(data):
        return ('VEFT' in data['orgaoJulgador'])
    def fiscal5(data):
        return ('Central de Avaliação e Arrematação' in data['orgaoJulgador'])
    def fiscal6(data):
        return (data['classeProcesso'] == 1116)
    def fiscal7(data):
        return (data['classeProcesso'] == 1118)
    
    # Funções para a Administrativa
    def adm1(data):
        return ('10299' in data['assuntos'])
    
    # Funções para a Judicial
    def jud1(data):
        return ('9992' in data['assuntos'])
    def jud2(data):
        return ('10433' in data['assuntos'])
    def jud3(data):
        return ('10502' in data['assuntos'])
    def jud4(data):
        return ('9992' in data['assuntos'] and '10502' in data['assuntos'])
    
    # Funções para a Patrimonial
    def pat1(data):
        return ('10458' in data['assuntos'])
    def pat2(data):
        return ('10121' in data['assuntos'])
    def pat3(data):
        return ('10459' in data['assuntos'])
    def pat4(data):
        return ('10457' in data['assuntos'])
    def pat5(data):
        return (data['classeProcesso'] == 49)
    def pat6(data):
        return (data['classeProcesso'] == 90)
    
    # Funções para a Saúde
    def saude1(data):
        return ('12500' in data['assuntos'])
    def saude2(data):
        return ('12485' in data['assuntos'])
    def saude3(data):
        return ('12491' in data['assuntos'])
    def saude4(data):
        return ('12494' in data['assuntos'])
    def saude5(data):
        return ('12501' in data['assuntos'])
    def saude6(data):
        return ('12503' in data['assuntos'])
    def saude7(data):
        return ('12511' in data['assuntos'])
    def saude8(data):
        return (data['classeProcesso'] == 1706)

    # Criando o classificador de regras
    rule_clf = RuleBasedClassifier()
    
    rule_clf.add_rule(Rule(funcao=fiscal1, nome='Fiscal - Assunto 5952', consequente=ClassLabel.FISCAL))
    rule_clf.add_rule(Rule(funcao=fiscal2, nome='Fiscal - Assunto 10536', consequente=ClassLabel.FISCAL))
    rule_clf.add_rule(Rule(funcao=fiscal3, nome='Fiscal - Assuntos 5952 e 10536', consequente=ClassLabel.FISCAL))
    rule_clf.add_rule(Rule(funcao=fiscal4, nome='Fiscal - Órgão VEFT', consequente=ClassLabel.FISCAL))
    rule_clf.add_rule(Rule(funcao=fiscal5, nome='Fiscal - Central Avaliação e Arrematação', consequente=ClassLabel.FISCAL))
    rule_clf.add_rule(Rule(funcao=fiscal6, nome='Fiscal - Classe Processo 1116', consequente=ClassLabel.FISCAL))
    rule_clf.add_rule(Rule(funcao=fiscal7, nome='Fiscal - Classe Processo 1118', consequente=ClassLabel.FISCAL))

    # Regras para Administrativa
    rule_clf.add_rule(Rule(funcao=adm1, nome='Administrativa - Assunto 10299', consequente=ClassLabel.ADMINISTRATIVA))

    # Regras para Judicial
    rule_clf.add_rule(Rule(funcao=jud1, nome='Judicial - Assunto 9992', consequente=ClassLabel.JUDICIAL))
    rule_clf.add_rule(Rule(funcao=jud2, nome='Judicial - Assunto 10433', consequente=ClassLabel.JUDICIAL))
    rule_clf.add_rule(Rule(funcao=jud3, nome='Judicial - Assunto 10502', consequente=ClassLabel.JUDICIAL))
    rule_clf.add_rule(Rule(funcao=jud4, nome='Judicial - Assuntos 9992 e 10502', consequente=ClassLabel.JUDICIAL))

    # Regras para Patrimonial
    rule_clf.add_rule(Rule(funcao=pat1, nome='Patrimonial - Assunto 10458', consequente=ClassLabel.PATRIMONIAL))
    rule_clf.add_rule(Rule(funcao=pat2, nome='Patrimonial - Assunto 10121', consequente=ClassLabel.PATRIMONIAL))
    rule_clf.add_rule(Rule(funcao=pat3, nome='Patrimonial - Assunto 10459', consequente=ClassLabel.PATRIMONIAL))
    rule_clf.add_rule(Rule(funcao=pat4, nome='Patrimonial - Assunto 10457', consequente=ClassLabel.PATRIMONIAL))
    rule_clf.add_rule(Rule(funcao=pat5, nome='Patrimonial - Classe Processo 49', consequente=ClassLabel.PATRIMONIAL))
    rule_clf.add_rule(Rule(funcao=pat6, nome='Patrimonial - Classe Processo 90', consequente=ClassLabel.PATRIMONIAL))

    # Regras para Saúde
    rule_clf.add_rule(Rule(funcao=saude1, nome='Saúde - Assunto 12500', consequente=ClassLabel.SAUDE))
    rule_clf.add_rule(Rule(funcao=saude2, nome='Saúde - Assunto 12485', consequente=ClassLabel.SAUDE))
    rule_clf.add_rule(Rule(funcao=saude3, nome='Saúde - Assunto 12491', consequente=ClassLabel.SAUDE))
    rule_clf.add_rule(Rule(funcao=saude4, nome='Saúde - Assunto 12494', consequente=ClassLabel.SAUDE))
    rule_clf.add_rule(Rule(funcao=saude5, nome='Saúde - Assunto 12501', consequente=ClassLabel.SAUDE))
    rule_clf.add_rule(Rule(funcao=saude6, nome='Saúde - Assunto 12503', consequente=ClassLabel.SAUDE))
    rule_clf.add_rule(Rule(funcao=saude7, nome='Saúde - Assunto 12511', consequente=ClassLabel.SAUDE))
    rule_clf.add_rule(Rule(funcao=saude8, nome='Saúde - Classe Processo 1706', consequente=ClassLabel.SAUDE))

    rule_clf.train(data=X_train)
    y_pred = rule_clf.predict(data=X_test)

    pprint.pprint(rule_clf.calcular_metricas(), sort_dicts=False, width=100)

    print(y_pred[:5], [data['setorDestino'] for data in X_test[:5]])

if __name__ == '__main__':
    main()