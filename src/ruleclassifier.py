from sklearn.metrics import accuracy_score

class RuleClassifier:
    """
    Classificador baseado em regras para determinar o 'setorDestino'.

    Esta classe *simula* um classificador baseado em regras. Em uma aplicação
    real, você carregaria os dados, pré-processaria, extrairia as regras
    (conforme a metodologia descrita anteriormente) e, então, implementaria
    essas regras aqui.  Este código é um ESQUELETO para demonstrar como
    essas regras poderiam ser codificadas, uma vez extraídas.
    """

    def __init__(self):
        self.rules = []  # Lista para armazenar as regras
        self.rule_counts = {}

    def add_rule(self, condition_func, sector, rule_name=None):
        """
        Adiciona uma regra ao classificador.

        Args:
            condition_func: Função que retorna True/False para a condição.
            sector: O setor de destino a ser atribuído.
            rule_name: Nome opcional para a regra (para rastreamento).
        """
        if rule_name is None:
            rule_name = f"rule_{len(self.rules) + 1}"  # Nome padrão
        self.rules.append((condition_func, sector, rule_name))
        self.rule_counts[rule_name] = 0  # Inicializa contagem

    def classify(self, data_row):
        """
        Classifica uma única linha de dados.

        Args:
            data_row: Dicionário representando uma linha do DataFrame.

        Returns:
            O setor de destino previsto ou None se nenhuma regra se aplicar.
        """
        for condition_func, sector, rule_name in self.rules:
            if condition_func(data_row):
                self.rule_counts[rule_name] += 1  # Incrementa a contagem
                return sector
        return 'No Class'

    def classify_dataframe(self, df):
        """
        Classifica todas as linhas de um DataFrame.

        Args:
            df: O DataFrame pandas a ser classificado.

        Returns:
            Lista com os setores de destino previstos.
        """
        # Zera as contagens antes de classificar um novo DataFrame
        for rule_name in self.rule_counts:
            self.rule_counts[rule_name] = 0

        return [self.classify(row) for row in df.to_dict('records')]

    def evaluate(self, X_test, y_test):
         """
        Avalia o classificador, calculando métricas.
        Args:
            X_test: Um DataFrame com as colunas de entrada do conjunto de teste.
            y_test: Um DataFrame com os rótulos verdadeiros.

        Returns:
             Métricas de avaliação do modelo.
         """

         y_pred = self.classify_dataframe(X_test)
         accuracy = accuracy_score(y_test, y_pred)

         return accuracy, y_pred

    def get_rule_counts(self):
        """Retorna um dicionário com a contagem de aplicações de cada regra."""
        return self.rule_counts