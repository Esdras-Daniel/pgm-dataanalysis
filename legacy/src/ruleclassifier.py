from typing import Callable, Any, List, Dict
import pandas as pd

class Regra:
    def __init__(self, nome: str, funcao: Callable[[Any], bool], prioridade: int, consequente: Any):
        self.nome = nome
        self.funcao = funcao
        self.prioridade = prioridade
        self.consequente = consequente
        self.aplicacoes = 0  # Contador de quantas vezes a regra foi aplicada
        self.total_avaliacoes = 0  # Contador de quantas vezes a regra foi avaliada
    
    def avaliar(self, entrada: Any) -> bool:
        try:
            self.total_avaliacoes += 1
            resultado = self.funcao(entrada)
            if resultado:
                self.aplicacoes += 1
            return resultado
        except Exception as e:
            print(f"Erro ao avaliar a regra '{self.nome}': {e}")
            return False
    
    def acuracia(self) -> float:
        return (self.aplicacoes / self.total_avaliacoes) * 100 if self.total_avaliacoes > 0 else 0.0

class ClassificadorBaseadoEmRegras:
    def __init__(self):
        self.regras: List[Regra] = []
    
    def adicionar_regra(self, nome: str, funcao: Callable[[Any], bool], prioridade: int, consequente: Any):
        if not callable(funcao):
            raise ValueError("A função da regra deve ser callable.")
        regra = Regra(nome, funcao, prioridade, consequente)
        self.regras.append(regra)
        self.regras.sort(key=lambda r: r.prioridade, reverse=True)  # Ordena por prioridade
    
    def classificar(self, entrada: Any) -> List[Any]:
        if isinstance(entrada, pd.DataFrame):
            return self.classificar_dataframe(entrada)
        
        if not isinstance(entrada, dict):
            raise TypeError("A entrada deve ser um dicionário ou um DataFrame.")
        
        resultados = []
        for regra in self.regras:
            if regra.avaliar(entrada):
                resultados.append((regra.nome, regra.consequena.consequente))
        return resultados
    
    def classificar_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        resultados = []
        for _, row in df.iterrows():
            classificacoes = self.classificar(row.to_dict())
            resultados.append([c[1] for c in classificacoes])
        df["Classificação"] = resultados
        return df
    
    def estatisticas(self) -> Dict[str, Dict[str, Any]]:
        return {
            regra.nome: {
                "aplicacoes": regra.aplicacoes,
                "total_avaliacoes": regra.total_avaliacoes,
                "acuracia": regra.acuracia()
            }
            for regra in self.regras
        }