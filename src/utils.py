import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import time
import os
from sklearn.metrics import confusion_matrix

def separa_assuntos_documentos(itens_list: pd.Series, sep=';'):

    data = []

    # Popula uma lista com as separações
    for item in itens_list:
        try:
            data.append(str(item).split(sep))
        except AttributeError as error:
            print(f'Erro ao processar "{item}": {error}')
        #data.append(item.split(sep))
        '''if isinstance(item, str):
            data.append(item.split(sep))
        else:
            data.append([])'''

    # Obtendo todos os números únicos como colunas
    cols = sorted(set(num for sublist in data for num in sublist))
    print(f'Número de assuntos/documentos: {len(cols)}')

    # Criando o DataFrame Binário
    df = pd.DataFrame([{col: (col in row) * 1 for col in cols} for row in data])

    return df

def save_csv(df: pd.DataFrame, file_name: str):
    if file_name is None:
        raise ValueError('Insira nome do arquivo para ser salvo')
    
    path = f'./data/{file_name}'

    if os.path.exists(path):
        print(f'Arquivo "{path}" já existe!')
        
        return None

    df.to_csv(path)

def plot_confusion_matrix(y_true, y_pred, class_names):
    # Recupera os nomes das classes reais
    classes_reais = sorted(set(y_true))

    # Recupera os nomes das classes preditas
    classes_pred = sorted(set(y_pred))

    # Cria a matriz de confusão
    cm = np.zeros(shape=(len(classes_reais), len(classes_pred)), dtype=int)

    # Preencher a matriz de confusão
    for real, previsto in zip(y_true, y_pred):
        i = classes_reais.index(real)   # Índice da classe real
        j = classes_pred.index(previsto) # Índice da classe prevista
        cm[i, j] += 1  # Incrementar contagem na posição correta
    
    # Normaliza a matriz para valores entre 0 e 1
    cm_normalized = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
    
    # Cria o gráfico
    plt.figure(figsize=(10, 8))
    plt.imshow(cm_normalized, interpolation='nearest', cmap=plt.cm.Blues)
    plt.title('Matriz de Confusão', fontsize=16)
    plt.colorbar()
    
    # Adiciona rótulos
    tick_marks = np.arange(len(class_names))
    plt.xticks(np.arange(len(classes_pred)), classes_pred, rotation=45, fontsize=6)
    plt.yticks(np.arange(len(classes_reais)), classes_reais, fontsize=8)
    
    # Adiciona os valores na matriz
    thresh = cm_normalized.max() / 2.
    for i, j in np.ndindex(cm_normalized.shape):
        plt.text(j, i, f'{cm[i, j]}\n\n({cm_normalized[i, j]*100:.2f})',
                 horizontalalignment="center",
                 color="white" if cm_normalized[i, j] > thresh else "black",
                 fontsize=10)
    
    plt.ylabel('Classe Real', fontsize=14)
    plt.xlabel('Classe Prevista', fontsize=14)
    plt.tight_layout()
    plt.show()

def evaluate_classifiers(classifiers, X_train, y_train, X_test, y_test, class_names):
    """
    Treina e avalia uma sequência de classificadores, exibindo o tempo de treinamento e as matrizes de confusão.
    
    :param classifiers: Lista de tuplas (nome, modelo) com os classificadores do scikit-learn.
    :param X_train: Conjunto de treinamento (features).
    :param y_train: Labels do conjunto de treinamento.
    :param X_test: Conjunto de teste (features).
    :param y_test: Labels do conjunto de teste.
    :param class_names: Lista com os nomes das classes.
    """
    num_classifiers = len(classifiers)
    cols = 3
    rows = (num_classifiers + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(5 * cols, 5 * rows))
    axes = axes.flatten()
    
    for ax, (name, clf) in zip(axes, classifiers):
        start_time = time.time()
        clf.fit(X_train, y_train)
        train_time = time.time() - start_time
        
        y_pred = clf.predict(X_test)
        cm = confusion_matrix(y_test, y_pred)
        cm_normalized = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]

        accuracy = np.trace(cm) / np.sum(cm)
        recall = np.mean(np.diag(cm) / np.sum(cm, axis=1))
        
        ax.imshow(cm_normalized, interpolation='nearest', cmap=plt.cm.Blues)
        ax.set_title(f'{name}\nTempo: {train_time:.2f}s', fontsize=14)
        ax.set_xticks(np.arange(len(class_names)))
        ax.set_yticks(np.arange(len(class_names)))
        ax.set_xticklabels(class_names, rotation=45, fontsize=8)
        ax.set_yticklabels(class_names, fontsize=8)
        ax.set_ylabel('Classe Real', fontsize=12)
        ax.set_xlabel('Classe Prevista', fontsize=12)
        
        thresh = cm_normalized.max() / 2.
        for i, j in np.ndindex(cm.shape):
            ax.text(j, i, f'{cm[i, j]}\n({cm_normalized[i, j]*100:.2f}%)',
                    horizontalalignment="center",
                    color="white" if cm_normalized[i, j] > thresh else "black",
                    fontsize=10)
        
        ax.text(0.5, -0.3, f'Acurácia: {accuracy*100:.2f}%\nRecall: {recall*100:.2f}%',
                horizontalalignment='center', verticalalignment='center',
                transform=ax.transAxes, fontsize=12, color='black', fontweight='bold')
    
    for ax in axes[num_classifiers:]:
        ax.axis('off')
    
    plt.tight_layout()
    plt.show()

