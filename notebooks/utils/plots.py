import matplotlib.pyplot as plt
import seaborn as sns
from mlxtend.frequent_patterns import apriori
from sklearn.metrics import confusion_matrix
import pandas as pd
import numpy as np

def plot_most_subjects_per_class(df: pd.DataFrame, N:int=6, fontsize=8):
    """
    Plota gráficos de pizza para os assuntos mais frequentes de cada classe.

    A função recebe um DataFrame em que cada linha representa uma classe e cada coluna representa 
    a contagem de ocorrências de um determinado assunto. Para cada classe, ela seleciona os N assuntos 
    com maiores contagens e agrupa os restantes na categoria "Outros". Em seguida, cria um gráfico de pizza 
    para cada classe, exibindo a distribuição percentual dos assuntos, com a contagem absoluta exibida em cada fatia.

    Parâmetros:
    -----------
    df : pandas.DataFrame
        DataFrame onde cada linha representa uma classe e as colunas correspondem aos diferentes assuntos 
        com suas respectivas contagens.
    N : int, opcional (padrão=6)
        Número de assuntos principais a serem destacados individualmente no gráfico. Os demais assuntos 
        serão agrupados na categoria "Outros".

    Retorno:
    --------
    None
        A função gera e exibe os gráficos de pizza utilizando matplotlib, sem retornar nenhum valor.
    """

    def autopct_format(pct, all_vals):
        absolute = int(round(pct / 100. * sum(all_vals)))  # Calcula o valor real
        return f"{pct:.1f}%\n({absolute})"  # Retorna ambos formatados

    fig, axes = plt.subplots(3, 3, figsize=(12, 12))

    # Percorrendo as 9 classes e criando os gráficos
    for i, (classe, valores) in enumerate(df.iterrows()):
        ax = axes[i // 3, i % 3]
        
        # Pegando os N princiáis assuntos + 'Outros'
        top_N = valores.nlargest(N)
        outros = valores.drop(top_N.index).sum()

        # Criando o dicionário para o gráfico de pizza
        data_plot = top_N.to_dict()
        data_plot['Outros'] = outros

         # Criando o gráfico
        ax.pie(data_plot.values(), labels=data_plot.keys(), autopct=lambda pct: autopct_format(pct, data_plot.values()), 
           colors=plt.cm.Paired.colors, startangle=90, textprops={'fontsize': fontsize})
        ax.set_title(f"Classe {classe}")
    
    plt.tight_layout()
    plt.show()

def plot_apriori_rules(df:pd.DataFrame, threshold:float = 0.3):
    # Verifica se 'setorDestino' está no DataFrame
    if 'setorDestino' not in df.columns:
        raise KeyError('Coluna "setorDestino" não existe no DataFrame')

    classes = np.unique(df['setorDestino'])
    fig, axes = plt.subplots(3, 3, figsize=(12, 12))
    
    for i, classe in enumerate(classes):
        ax = axes[i // 3, i % 3]

        df_select = df[df['setorDestino'] == classe].drop(columns=['setorDestino'])
        qtd_text = len(df_select)
        df_rules = apriori(df=df_select, min_support=threshold, use_colnames=True)
        
        # Caso o DataFrame esteja vazio, exibe uma mensagem no subplot
        if df_rules.empty:
            ax.text(0.5, 0.5, "Nenhuma regra encontrada", ha="center", va="center", fontsize=12)
            ax.set_xticks([])
            ax.set_yticks([])
            ax.set_title(f"Classe {classe}")
            continue

        # Ordena as regras pelo suporte de forma decrescente
        df_rules = df_rules.sort_values('support', ascending=True)

        # Preparar os dados
        itemsets = [', '.join(list(fset)) for fset in df_rules['itemsets']]
        supports = df_rules['support'].tolist()

        # Criando gráfico de barras horizontal
        bars = ax.barh(range(len(itemsets)), supports, color='skyblue')
    
        ax.set_yticks(range(len(itemsets)))
        ax.set_yticklabels(itemsets, fontsize=8)
        ax.set_xticks([])
        ax.set_title(f"Classe {classe}")
        
        # Exibe o valor do suporte dentro das barras de forma legível
        for bar, sup, label in zip(bars, supports, itemsets):
            text_x = max(bar.get_width() * 0.5, 0.1)  # Garante que o texto nunca fique muito à esquerda
            ax.text(text_x, bar.get_y() + bar.get_height()/2, 
                    f"{sup*100:.2f}%\n({int(qtd_text*sup)} textos)", 
                    ha='center', 
                    va='center', fontsize=8, weight='bold', color='black')
    
    plt.tight_layout()
    plt.show()
