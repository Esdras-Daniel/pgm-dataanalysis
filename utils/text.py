import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
nltk.download('stopwords')
import re
import unicodedata
from nltk.stem import RSLPStemmer

# Lista de stopwords do português
stop_words_pt = set(stopwords.words('portuguese'))

# Stemmer para português
stemmer = RSLPStemmer()

def normaliza_texto(text, use_stemming=False):
    """Retorna o texto padronizado para processamento. Remove ancentuação e pontuações e substitui
       padrões identificados previamente no texto.
    """

    if isinstance(text, float):  # Lidar com possíveis valores NaN
        return ""
    
    # Dicionário de substituições de termos
    '''substituicoes = {
        "Vara de Execução Fiscal e Tributária": "VEFT",
        "Vara da Fazenda Pública": "VFP",
        "Vara da Infância e Juventude": "VIJ",
        "Vara Cível": "VC",
        "Vara de Família e Sucessões": "VF e S",
        "Juizado da Fazenda Pública": "JFP",
        "Juizado Especial da Fazenda Pública": "JEFP",
        "Juizado Especial Cível, Criminal e da Fazenda Pública": "JECFP",
        "Gabinete": "Gab.",
        "Des.": "Des.",
        "Juiz": "J.",
        "Presidente": "Pres.",
        "Câmara Cível": "CC",
        "Turma Recursal": "TR",
        "Comarca de Natal": "Com NAT",
        "Comarca de Mossoró": "Com MOS",
        "Comarca de Parelhas": "Com PAR",
        "Comarca de São Miguel": "Com SMG",
        "Comarca de Apodi": "Com APO",
        "Comarca de Touros": "Com TOU",
        "Comarca de Currais Novos": "Com CN",
        "Pleno": "PL"
    }

    for chave, valor in substituicoes.items():
        text = text.replace(chave, valor)
    '''

    # Substituição de padrões específicos (antes da stemização/lematização)
    
    #text = re.sub(r'PODER\s+JUDICI[ÁA]RIO\s+(?:DO\s+)?(ESTADO\s+)?(?:DO\s+)?RIO\s+GRANDE\s+(?:DO\s+)?NORTE', 'TJRN', text, flags=re.IGNORECASE)
    #text = re.sub(r"proc\.?\s*nº", "[PROCESSO]", text, flags=re.IGNORECASE)
    #text = re.sub(r"\bexq\b\.?:", "[EXEQUENTE]", text, flags=re.IGNORECASE)
    #text = re.sub(r"\bexc\b\.?:", "[EXECUTADO]", text, flags=re.IGNORECASE)
    #text = re.sub(r"\bato\s+ordinat[oó]rio\b", "[ATO_ORDINATORIO]", text, flags=re.IGNORECASE)
    #text = re.sub(r"\bendere[cç]o\b", "[ENDERECO]", text, flags=re.IGNORECASE)
    #text = re.sub(r"(?<!\d)(\d{7}-\d{2}\.\d{4}\.\d{1,2}\.\d{2,4}\.\d{4})(?!\d)", "[NUMERO_PROCESSO]", text) # Números de processo maiores
    #text = re.sub(r"(?<!\d)(\d{1,2}/\d{1,2}/\d{2,4})(?!\d)", "[DATA]", text)  # Datas
    #text = re.sub(r"(?<!\d)(\d{5}-\d{3})(?!\d)", '[CEP]', text)
    #text = re.sub(r"(\(\d{2,3}\)\s?)?\d{4,5}-?\d{4}", "[TELEFONE]", text)
    #text = re.sub(r"pjrn", "[TJRN]", text, flags=re.IGNORECASE) #tribunal
    #text = re.sub(r"\b[rv]eft\b", "[VARA_EXECUCAO]", text, flags=re.IGNORECASE) #vara
     # Substitui várias ocorrências de "CERTIDÃO DE DÍVIDA ATIVA" por um único token
    #text = re.sub(r"(certid[ãa]o de d[ií]vida ativa\s*){2,}", "[CDA_MULTIPLE] ", text, flags=re.IGNORECASE)
    #text = re.sub(r"certid[ãa]o de d[ií]vida ativa", "[CDA]", text, flags=re.IGNORECASE)
    #text = re.sub(r'[^\w\s\[\]]', '', text)

    text_tokens = word_tokenize(text, language='portuguese')

    filtered_text = [word for word in text_tokens if word.lower() not in stop_words_pt and len(word) > 2]
    text = ' '.join(filtered_text)

    # Retira acentos e converte o texto
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII').lower()

    # Remoções de alguns termos
    padroes = [
        'poder judiciario do estado do rio grande do norte',
        'poder judiciario estado do rio grande do norte',
        'poder judiciario do estado rio grande do norte',
        'poder judiciario estado rio grande do norte',
        'normal', 'false', 'ptbr', 'xnone', 'poder', 'judiciario',
        'estado', 'rio', 'grande', 'norte', 'vara execucao fiscal',
        'tributaria natal', 'praca sete setembro','cidade alta',
        'natalrn', 'cep', 'rn', 'natal', '5902530', 'assinado', 'digitalmente',
        'forma lei', 'n1141906', 'comarca', 'forum fazendario', 'juiz djanirito souza moura',
        'data registrada sistema', '1141906', 'veft', '59025275', 'email', 'secuniefttj', 'jusbr',
        'telefone', 'whatsapp', '36738671', 'judiciario', 'natalpraca', 'setembro', 'cidade', '59025300',
        'rio norte', 'forum fazendario', 'juiz', 'djanirito souza mouro', 'praca alto', 'natalrn', 'nao',
        # Palavras escluidas após a conversa com Nailton dia 07/01/25
        'lei',
        '(?<!\d)(\d{7}-\d{2}\.\d{4}\.\d{1,2}\.\d{2,4}\.\d{4})(?!\d)', # Número do processo
        '(?<!\d)(\d{5}-\d{3})(?!\d)', # CEP
        '(?<!\d)(\d{1,2}/\d{1,2}/\d{2,4})(?!\d)' # Datas
    ]
    
    for padrao in padroes:
        text = re.sub(padrao, '', text, flags=re.IGNORECASE)

    # Stemização (opcional)
    if use_stemming:
        words = text.split()
        stemmed_words = [stemmer.stem(w) for w in words]
        text = " ".join(stemmed_words)

    return ' '.join(text.split())