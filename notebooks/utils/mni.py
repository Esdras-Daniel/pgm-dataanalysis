# === LINKS DA DOCUMENTAÇÃO
# https://www.pje.jus.br/wiki/index.php/Utiliza%C3%A7%C3%A3o_do_PJe
# https://www.pje.jus.br/wiki/index.php/Tutorial_MNI
# https://docs.pje.jus.br/
# pje1g-integracao.tse.jus.br
# ====

# === organizar as datas
import datetime
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning
from lxml import etree
from functools import reduce
import traceback
import json
import re
from bs4 import BeautifulSoup
import html

# === pandas para gerar a tabela de dados
import pandas as pd

# === Biblioteca para fazer requisições http
from requests import Session
from requests.auth import HTTPBasicAuth

# biblioteca para gerar uma conexão com o 
# protocolo SOAP que é o utilizado no MNI
try:
    from zeep.transports import Transport
    from zeep.plugins import HistoryPlugin
    import zeep
    from zeep.helpers import serialize_object
except:
    print('Por favor, instale a biblioteca zeep:\npip install zeep')

try:
    import xmltodict
except:
    print('Por favor, instale a biblioteca xmltodict:\npip install xmltodict')

disable_warnings(InsecureRequestWarning)

import warnings
warnings.filterwarnings('ignore')
# warnings.filterwarnings(action='once')


# === UTILIDADES
def remover_espacos_duplos(texto):
    '''Remove espaços duplos de uma string'''
    import re
    try:
        return " ".join(re.split(r"\s+", texto))
    except:
        return texto


def deep_get(dictionary, keys, default=''):
    '''Retorna o valor de um dicionário aninhado, caso não encontre retorna o valor default'''
    
    return reduce(lambda d, key: d.get(key, default) if isinstance(d, dict) else default, keys.split("."), dictionary)


def formatar_data_sem_mascara(date_time_str=None, formato_origem='%Y%m%d%H%M%S', formato_final='%d/%m/%Y - %H:%M:%S'):

    try:
        if date_time_str:
            date_time_obj = datetime.datetime.strptime(date_time_str, formato_origem)
            return date_time_obj.strftime(formato_final)
        else:
            return None
    except Exception as e:
        print(f'ERRO / formatar_data_sem_mascara: {e}')
        return None

def format_date_br(
    date_time_str=None,
    formato_origem='%Y%m%d%H%M%S',
    formato_final='%d/%m/%Y - %H:%M:%S'
):

    try:
        if date_time_str:
            date_time_obj = datetime.datetime.strptime(date_time_str, formato_origem)
            return date_time_obj.strftime(formato_final)
        else:
            return date_time_str
    except:
        return date_time_str

def create_timeline(case_data: dict) -> list:
    
    timeline = []

    movimentos = case_data.get('Movimentos', [])
    documentos = case_data.get('Documentos', [])
    documentos_vinculados = case_data.get('Descricao-Documentos', [])

    if isinstance(movimentos, str):
        try:
            movimentos = json.loads(movimentos)
        except:
            movimentos = []

    if isinstance(documentos, str):
        try:
            documentos = json.loads(documentos)
        except:
            documentos = []

    if isinstance(documentos_vinculados, str):
        try:
            documentos_vinculados = json.loads(documentos_vinculados)
        except:
            documentos_vinculados = []

    # Adiciona movimentos à linha do tempo
    for mov in movimentos:
        if isinstance(mov, dict):  # Verificar se mov é um dicionário
            timeline.append({
                'Tipo': '📢 Movimento',
                'Descrição': '📢 - ' + mov['Complemento'],
                'Data': mov['Data-Hora'],
            })

    # Adiciona documentos à linha do tempo
    for doc in documentos:
        if isinstance(doc, dict):  # Verificar se doc é um dicionário
            timeline.append({
                'Tipo': '📑 Documento',
                'Descrição': '📑 ' + doc['Descricao'] + ' | ID ' + doc['ID-Documento'],
                'Data': doc['Data-Hora']
            })
        # Adiciona documentos vinculados à linha do tempo
        for doc_vinc in documentos_vinculados:
            if isinstance(doc_vinc, dict):  # Verificar se doc_vinc é um dicionário
                timeline.append({
                    'Tipo': '📌 Documento Vinculado',
                    'Descrição': '    📌 ' + doc_vinc['Descricao'],
                    'Data': doc_vinc['Data-Hora']
                })

    # Ordena a linha do tempo por data e hora
    timeline.sort(key=lambda x: x['Data'], reverse=True)

    # agora eu quero formatar a data e hora com a função format_date_br
    for item in timeline:
        item['Data'] = f"{item['Data']} || {format_date_br(item['Data'])}"

    return timeline

# === PARSE


# === SERVIÇOS MNI
def consulta_processo_mni(
    num_processo_com_mascara,
    wsdl=None,
    id_pje=None,
    pass_pje=None,
    apartir_de_data="",
    movimentos=True,
    cabecalho=True,
    documentos=False,
    timeout=30):

    try:
        '''
        Caso tenha problemas de ssl
        '''
        session = Session()
        session.verify = False

        if not id_pje or not pass_pje:
            return False, 'Credencial de Acesso não informada.'
        if not wsdl:
            return False, 'Ausente link do wsdl'

        if num_processo_com_mascara.find('.') != -1:
            num_processo_com_mascara = num_processo_com_mascara.replace('-', '').replace('.', '')

        session.auth = HTTPBasicAuth(id_pje, pass_pje)
        session.headers = {"Content-Type": "text/xml;charset=UTF-8"}

        transport = Transport(session=session, timeout=timeout)
        settings = zeep.Settings(strict=False, xml_huge_tree=True)
        history = HistoryPlugin()
        client = zeep.Client(wsdl=wsdl, transport=transport, settings=settings, plugins=[history])

        if apartir_de_data != '':
            apartir_de_data = datetime.datetime.strptime(apartir_de_data, "%d/%m/%Y")

        # utiliza a função do soap
        resp = client.service.consultarProcesso(
            idConsultante=id_pje,
            senhaConsultante=pass_pje,
            numeroProcesso=num_processo_com_mascara,
            dataReferencia=apartir_de_data,
            movimentos=movimentos,
            incluirCabecalho=cabecalho,
            incluirDocumentos=documentos
        )

        pretty_xml = etree.tostring(
            history.last_received["envelope"], 
            encoding="unicode", 
            pretty_print=True
        )

        # Caso a conexão seja um sucesso
        if resp['sucesso'] is True:

            # remover_espacos_duplos(pretty_xml)
            return True, pretty_xml 
        else:
            return False, resp

    except Exception as e:
        
        falha_msg = f'Falha: {e} - {traceback.print_exc()}'           

        return None, falha_msg


def consulta_avisos_pendentes_mni(
    link_pje=None,
    id_pje=None,
    pass_pje=None,
    apartir_de_data="",
    timeout=30,
    ):

    try:
        session = Session()
        session.verify = False

        if not id_pje or not pass_pje:
            return False, 'Credencial de Acesso não informada.'

        session.auth = HTTPBasicAuth(id_pje, pass_pje)

        transport = Transport(session=session, timeout=timeout)
        settings = zeep.Settings(strict=False, xml_huge_tree=True)
        history = HistoryPlugin()
        client = zeep.Client(
            wsdl=link_pje, transport=transport, settings=settings, plugins=[history]
        )

        if apartir_de_data != '':
            # Transforma a string de data em timestamp
            apartir_de_data = datetime.datetime.strptime(apartir_de_data, "%d/%m/%Y")

        # utiliza a função do soap
        resp = client.service.consultarAvisosPendentes(
            idConsultante=id_pje,
            senhaConsultante=pass_pje,
            dataReferencia=apartir_de_data,
            # tipoPendencia=tipo_pendencia,
            )

        pretty_xml = etree.tostring(
            history.last_received["envelope"], 
            encoding="unicode", pretty_print=True
        )

        # Caso a conexão seja um sucesso
        if resp['sucesso'] is True:
            # remover_espacos_duplos(pretty_xml)
            return True, pretty_xml 
        else:
            return False, resp

    except Exception as e:
        
        falha_msg = f'Falha: {e} - {traceback.print_exc()}'           

        return None, falha_msg


# https://www.cnj.jus.br/sgt/infWebService.php
def pesquisar_nome_classe_processual_cnj(
    tipoTabela='C', # Tipo da tabela a ser pesquisada(A,M,C) - Assuntos, Movimentos, Classes
    tipoPesquisa='C', # -Tipo da pesquisa(G,N,C) - Glossário, Nome, Código
    valorPesquisa='1116'
):
    
    # https://www.cnj.jus.br/sgt/infWebService.php
    settings = zeep.Settings(strict=False, xml_huge_tree=True)
    history = HistoryPlugin()
    client = zeep.Client(
        wsdl='https://www.cnj.jus.br/sgt/sgt_ws.php?wsdl', 
        settings=settings, plugins=[history]
    )

    try:
        # utiliza a função do soap
        resp = client.service.pesquisarItemPublicoWS(
            tipoTabela=tipoTabela,
            tipoPesquisa=tipoPesquisa,
            valorPesquisa=valorPesquisa
            )

        pretty_xml = etree.tostring(
            history.last_received["envelope"], 
            encoding="unicode", pretty_print=True
        )

        return resp, pretty_xml
    except Exception as e:
        return None, f'Falha: {e} - {traceback.print_exc()}'


# === parse avisos
def extrair_informacao_do_xml_avisos(xml_str, retornar_df=True):
    '''Extrai informações do XML de avisos pendentes'''

    try:
        #pattern_xml = r'(<soap:Envelope.*?</soap:Envelope>)'
        pattern = r'Content-ID.*?\n(.*?)--uuid'

        # Limpar conteúdo: localiza o bloco do XML e HTML
        blocos = re.findall(pattern, xml_str, flags=re.DOTALL | re.IGNORECASE)
        blocos = [m.strip() for m in blocos]
        
        bloco_xml = blocos[0]
        bloco_html = blocos[1]

        # Parse o XML
        try:
            dicionario = xmltodict.parse(bloco_xml)
        except Exception as e:
            print(f'ERRO ao fazer parse do XML: {e}')
            return pd.DataFrame() if retornar_df else []

        body = dicionario.get('soap:Envelope', {}).get('soap:Body', {})

        #print(body)
        #return body

        # Encontre a chave de resposta
        chave_resposta = next((k for k in body.keys() if 'consultarTeorComunicacaoResposta' in k), None)

        if not chave_resposta:
            return pd.DataFrame() if retornar_df else []

        resposta = body.get(chave_resposta, {})
        aviso = resposta.get('comunicacao', [])

        #return resposta

        mapa = {}

        # Prefixo 'ns' utilizado nos campos
        prefixo = next((k.split(':')[0] for k in aviso.keys() if ':' in k), '')

        # Extrai informações detalhadas do aviso
        mapa['ID'] = aviso.get('@id', '')
        mapa['Tipo-Comunicacao'] = aviso.get('@tipoComunicacao', '')
        mapa['Tipo-Prazo'] = aviso.get('@tipoPrazo', '')
        mapa['Data-Referencia'] = aviso.get('@dataReferencia', '')

        destinatario = aviso.get(f'{prefixo}:destinatario', {})
        pessoa = destinatario.get(f'{prefixo}:pessoa', {})
        mapa['Destinatário'] = pessoa.get('@nome', '')
        mapa['Tipo-Pessoa'] = pessoa.get('@tipoPessoa', '')
        mapa['Documento-Principal'] = pessoa.get('@numeroDocumentoPrincipal', '')

        mapa['Processo'] = aviso.get(f'{prefixo}:processo', '')

        documento = aviso.get(f'{prefixo}:documento', '')
        mapa['ID-Documento'] = documento.get('@idDocumento', '')
        mapa['Tipo-Documento'] = documento.get('@tipoDocumento', '')
        mapa['Data-Hora'] = documento.get('@dataHora', '')
        #processo = aviso.get(f'{prefixo}:processo', {})
        #mapa['Processo'] = processo.get('@numero', '')
        #mapa['Competencia'] = processo.get('@competencia', '')
        #mapa['Classe-Processual'] = processo.get('@classeProcessual', '')
        #mapa['Codigo-Localidade'] = processo.get('@codigoLocalidade', '')
        #mapa['Nivel-Sigilo'] = processo.get('@nivelSigilo', '')
        #mapa['Data-Ajuizamento'] = formatar_data_sem_mascara(processo.get('@dataAjuizamento', ''))

        #orgao_julgador = processo.get(f'{prefixo}:orgaoJulgador', {})
        #mapa['Origem'] = orgao_julgador.get('@nomeOrgao', '')
        #mapa['Codigo-Orgao'] = orgao_julgador.get('@codigoOrgao', '')
        #mapa['Instancia'] = orgao_julgador.get('@instancia', '')

        #mapa['Data-Expediente'] = formatar_data_sem_mascara(aviso.get(f'{prefixo}:dataDisponibilizacao', ''))

        #assunto = processo.get(f'{prefixo}:assunto', {})
        #mapa['Assunto-Codigo-Nacional'] = assunto.get(f'{prefixo}:codigoNacional', '')

        #mapa['Valor-Causa'] = processo.get(f'{prefixo}:valorCausa', '')

        # Recuperando o Texto
        soup = BeautifulSoup(bloco_html, 'html.parser')
        html_raw_text = soup.get_text()

        mapa['Teor-Texto'] = html.unescape(html_raw_text)

        if retornar_df:
            df = pd.DataFrame([mapa])
            return df
        #.sort_values(by='Data-Expediente', ascending=True) if not df.empty else pd.DataFrame()
        else:
            return mapa
        
    except Exception as e:
        print(f'[Aviso] Erro ao processar texto: {e}')
        return pd.DataFrame() if retornar_df else {}

# === parse processo
def verifica_cliente_demandado(
    processo, 
    nomes_clientes=[
        'Município de Natal',
        'INSTITUTO DE PREVIDENCIA DOS SERVIDORES DE NATAL'
    ]
):

    for nome_cliente in nomes_clientes:
        try:
            for polo in processo['Polos']:
                if polo['Polo'] == 'PA':
                    for parte in polo['Partes']:
                        if parte['Pessoa'].lower().find(nome_cliente.lower()) >= 0:
                            return True
        except:
            pass
    return False


def calcular_tempo_tramitacao(processo):
    data_ajuizamento_str = processo['Data-Ajuizamento'].split(' - ')[0]
    data_ajuizamento = datetime.datetime.strptime(data_ajuizamento_str, '%d/%m/%Y')
    data_atual = datetime.datetime.now()
    tempo_tramitacao = data_atual - data_ajuizamento
    return tempo_tramitacao.days


def identificar_movimentos_relevantes(processo):
    movimentos_relevantes = []
    for movimento in processo['Movimentos']:
        descricao = movimento.get('Complemento', '')
        if descricao:
            movimentos_relevantes.append(descricao)
    return movimentos_relevantes


def identificar_descricao_documentos(processo):
    descricoes_documentos_principais = []
    descricoes_documentos_vinculados = []

    for documento in processo['Documentos']:
        descricao = documento.get('Descricao', '')
        if descricao:
            descricoes_documentos_principais.append(descricao)

        for doc_vinculado in documento.get('Documentos-Vinculados', []):
            descricao_vinculada = doc_vinculado.get('Descricao', '')
            if descricao_vinculada:
                descricoes_documentos_vinculados.append(descricao_vinculada)

    return descricoes_documentos_principais, descricoes_documentos_vinculados


def verificar_documentos_principais(
    processo, 
    termos_relevantes = [
        'Sentença', 'Contestação', 
        'Apelação', 'Citação',
        'Embargos de Declaração',
        'Trânsito em Julgado'
    ]
):
    
    resultados = {termo: False for termo in termos_relevantes}

    documentos_principais, _ = identificar_descricao_documentos(processo)

    for descricao in documentos_principais:
        for termo in termos_relevantes:
            if termo.lower() in descricao.lower():
                resultados[termo] = True

    return resultados


def extrair_informacao_do_xml_processo(xml_str, retornar_df=True, simplificar=True):
    '''Extrai informações detalhadas do XML de processo'''

    try:
        # Parse o XML e converta para um dicionário
        dicionario = xmltodict.parse(xml_str)
        body = dicionario.get('soap:Envelope', {}).get('soap:Body', {})

        # Encontre a chave de resposta

        #chave_resposta = next((k for k in body.keys() if 'consultarProcessoResposta' in k), None)
        chave_resposta = next((k for k in dicionario.keys() if 'consultarProcessoResposta' in k), None)

        if not chave_resposta:
            return {} if retornar_df else {}

        #resposta = body.get(chave_resposta, {})
        resposta = dicionario.get(chave_resposta, {})
        #processo = resposta.get('processo', {})
        processo = resposta.get('ns1:processo', {})

        dados_basicos = processo.get('ns2:dadosBasicos', {})
        movimentos = processo.get('ns2:movimento', [])
        documentos = processo.get('ns2:documento', [])
        assuntos = dados_basicos.get('ns2:assunto', [])
        processos_vinculados = dados_basicos.get('ns2:processoVinculado', [])

        # Estrutura básica do processo
        processo_dados = {
            'Numero': dados_basicos.get('@numero', ''),
            'Competencia': dados_basicos.get('@competencia', ''),
            'Classe-Processual': dados_basicos.get('@classeProcessual', ''),
            'Codigo-Localidade': dados_basicos.get('@codigoLocalidade', ''),
            'Nivel-Sigilo': dados_basicos.get('@nivelSigilo', ''),
            'Data-Ajuizamento': formatar_data_sem_mascara(dados_basicos.get('@dataAjuizamento', '')),
            'Valor-Causa': dados_basicos.get('ns2:valorCausa', ''),
            'Magistrado-Atuante': dados_basicos.get('ns2:magistradoAtuante', ''),
            'Orgao-Julgador': dados_basicos.get('ns2:orgaoJulgador', {}).get('@nomeOrgao', ''),
            'Assuntos': [],
            'Processos-Vinculados': [],
            'Status-Processo': dados_basicos.get('@valor', ''),
        }

        if not processo_dados['Status-Processo']:
            try:
                processo_dados['Status-Processo'] = dados_basicos.get('ns2:outroParametro', {})[0].get('@valor', '')
            except KeyError:
                pass

        # Extração de assuntos
        if not isinstance(assuntos, list):
            assuntos = [assuntos]
        for assunto in assuntos:
            processo_dados['Assuntos'].append({
                'CodigoNacional': assunto.get('ns2:codigoNacional', ''),
                'Principal': assunto.get('@principal', 'false') == 'true'
            })

        # Extração de processos vinculados
        if not isinstance(processos_vinculados, list):
            processos_vinculados = [processos_vinculados]
        for vinculado in processos_vinculados:
            processo_dados['Processos-Vinculados'].append({
                'NumeroProcesso': vinculado.get('@numeroProcesso', ''),
                'Vinculo': vinculado.get('@vinculo', '')
            })

        # Extração de polos e partes
        polos = dados_basicos.get('ns2:polo', [])
        processo_dados['Polos'] = []

        if isinstance(polos, dict):
            polos = [polos]  # Transforma em lista se for um único dicionário

        for polo in polos:
            polo_data = {
                'Polo': polo.get('@polo', ''),
                'Partes': []
            }

            partes = polo.get('ns2:parte', [])
            if isinstance(partes, dict):
                partes = [partes]  # Transforma em lista se for um único dicionário

            for parte in partes:

                pessoa = parte.get('ns2:pessoa', {})
                parte_data = {
                    'Assistencia-Judiciaria': parte.get('@assistenciaJudiciaria', ''),
                    'Intimacao-Pendente': parte.get('@intimacaoPendente', ''),
                    'Pessoa': pessoa.get('@nome', ''),
                    'Tipo-Pessoa': pessoa.get('@tipoPessoa', ''),
                    'Documento-Principal': pessoa.get('@numeroDocumentoPrincipal', ''),
                    'Polo': polo.get('@polo', ''),
                    'Documentos': [],
                    'Endereco': pessoa.get('ns2:endereco', {}),
                    'Advogados': []
                }

                documentos_pessoa = pessoa.get('ns2:documento', [])
                if isinstance(documentos_pessoa, dict):
                    documentos_pessoa = [documentos_pessoa]  # Transforma em lista se for um único dicionário

                for documento in documentos_pessoa:
                    documento_data = {
                        'Codigo-Documento': documento.get('@codigoDocumento', ''),
                        'Emissor-Documento': documento.get('@emissorDocumento', ''),
                        'Tipo-Documento': documento.get('@tipoDocumento', ''),
                        'Nome-Documento': documento.get('@nome', '')
                    }
                    parte_data['Documentos'].append(documento_data)

                advogados = parte.get('ns2:advogado', [])
                if isinstance(advogados, dict):
                    advogados = [advogados]  # Transforma em lista se for um único dicionário

                for advogado in advogados:
                    advogado_data = {
                        'Nome': advogado.get('@nome', ''),
                        'Inscricao': advogado.get('@inscricao', ''),
                        'Numero-Documento-Principal': advogado.get('@numeroDocumentoPrincipal', '')
                    }
                    parte_data['Advogados'].append(advogado_data)

                polo_data['Partes'].append(parte_data)

            processo_dados['Polos'].append(polo_data)

        # Extração de movimentos
        processo_dados['Movimentos'] = []

        if isinstance(movimentos, dict):
            movimentos = [movimentos]  # Transforma em lista se for um único dicionário

        for movimento in movimentos:
            
            movimento_data = {
                'Data-Hora': movimento.get('@dataHora', ''),
                'Nivel-Sigilo': movimento.get('@nivelSigilo', ''),
                'Identificador-Movimento': movimento.get('@identificadorMovimento', ''),
                'Movimento-Nacional': movimento.get('ns2:movimentoNacional', {}).get('@codigoNacional', ''),
                'Complemento': movimento.get('ns2:movimentoNacional', {}).get('ns2:complemento', '')
            }
            processo_dados['Movimentos'].append(movimento_data)

        # organizar em ordem decrescente por data-hora
        try:
            df = pd.DataFrame(processo_dados['Movimentos'])
            df.sort_values(by='Data-Hora', ascending=False, inplace=True)
            processo_dados['Movimentos'] = df.to_dict(orient='records')
        except:
            pass
        finally:
            del df

        # === Extração de documentos
        processo_dados['Documentos'] = []

        if isinstance(documentos, dict):
            documentos = [documentos]  # Transforma em lista se for um único dicionário

        for documento in documentos:
            
            documento_data = {
                'ID-Documento': documento.get('@idDocumento', ''),
                'Tipo-Documento': documento.get('@tipoDocumento', ''),
                'Data-Hora': documento.get('@dataHora', ''),
                'Mimetype': documento.get('@mimetype', ''),
                'Nivel-Sigilo': documento.get('@nivelSigilo', ''),
                'Hash': documento.get('@hash', ''),
                'Descricao': documento.get('@descricao', '')
            }

            documentos_vinculados = documento.get('ns2:documentoVinculado', [])
            if isinstance(documentos_vinculados, dict):
                documentos_vinculados = [documentos_vinculados]  # Transforma em lista se for um único dicionário

            documento_data['Documentos-Vinculados'] = []

            for doc_vinculado in documentos_vinculados:
                doc_vinculado_data = {
                    'ID-Documento': doc_vinculado.get('@idDocumento', ''),
                    'ID-Documento-Vinculado': doc_vinculado.get('@idDocumentoVinculado', ''),
                    'Tipo-Documento': doc_vinculado.get('@tipoDocumento', ''),
                    'Data-Hora': doc_vinculado.get('@dataHora', ''),
                    'Mimetype': doc_vinculado.get('@mimetype', ''),
                    'Nivel-Sigilo': doc_vinculado.get('@nivelSigilo', ''),
                    'Hash': doc_vinculado.get('@hash', ''),
                    'Descricao': doc_vinculado.get('@descricao', '')
                }
                documento_data['Documentos-Vinculados'].append(doc_vinculado_data)

            processo_dados['Documentos'].append(documento_data)

        # organizar Documentos por data-hora em ordem decrescente
        try:
            df = pd.DataFrame(processo_dados['Documentos'])
            df.sort_values(by='Data-Hora', ascending=False, inplace=True)
            processo_dados['Documentos'] = df.to_dict(orient='records')
        except:
            pass
        finally:
            del df

        if simplificar is True:
            # if Timeline is not None, remove it
            if 'Timeline' in processo_dados:
                processo_dados.pop('Timeline', None)
            if 'Movimentos' in processo_dados:
                processo_dados.pop('Documentos', None)
        else:
            processo_dados['Timeline'] = create_timeline(processo_dados)

        #processo_dados['Municipio-Reu'] = verifica_cliente_demandado(processo_dados)
        processo_dados['Tempo-Tramitacao'] = calcular_tempo_tramitacao(processo_dados)
        #processo_dados['Movimentos-Relevantes'] = identificar_movimentos_relevantes(processo_dados)
        #processo_dados['Descricao-Documentos'] = identificar_descricao_documentos(processo_dados)
        #processo_dados['Termos-Relevantes'] = verificar_documentos_principais(processo_dados)

        if retornar_df:
            # Retornar como DataFrame, mas isso pode ser complexo devido à estrutura aninhada
            return pd.json_normalize(processo_dados, sep='_')
        else:
            return processo_dados
        
    except Exception as e:
        print(f'[Processo] Erro ao processar XML: {e}')
        return pd.DataFrame() if retornar_df else {}


if __name__ == "__main__":

    # !pip install pandas requests zeep xmltodict
    # 0807483-73.2024.8.19.0011 - TJRJ
    # 0824489-24.2024.8.18.0140 - TJPI
    import os

    id_pje   = os.environ['MNI_USER']
    pass_pje = os.environ['MNI_PASS']
    wsdl     = 'https://tjrj.pje.jus.br/1g/intercomunicacao?wsdl'
    num_processo_com_mascara = '08239332120248190002'

    deu_certo, xml_or_resp = consulta_processo_mni(
        num_processo_com_mascara,
        wsdl=wsdl,
        id_pje=id_pje,
        pass_pje=pass_pje,
        apartir_de_data="", # %d/%m/%Y
        movimentos=True,
        cabecalho=True,
        documentos=True,
        timeout=30
    )

    if deu_certo is True:
        # temos um xml para fazer parse
        print(extrair_informacao_do_xml_processo(xml_or_resp, retornar_df=False))
    else:
        print('Falhou\n----')
        print(xml_or_resp)