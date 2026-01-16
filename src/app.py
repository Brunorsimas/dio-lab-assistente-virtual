import json
import pandas as pd
import requests
import streamlit as st

# ============ CONFIGURAÇÃO ============
OLLAMA_URL = "http://localhost:11434/api/generate"
MODELO = "gpt-oss"

# ============ CARREGAR DADOS ============
perfil = json.load(open('./data/perfil_investidor.json'))
transacoes = pd.read_csv('./data/transacoes.csv')
historico = pd.read_csv('./data/historico_atendimento.csv')
produtos = json.load(open('./data/produtos_financeiros.json'))

# ============ MONTAR CONTEXTO ============
# Calcular métricas importantes para reserva de emergência
despesas_mensais = transacoes[transacoes['tipo'] == 'saida']['valor'].sum()
reserva_ideal = despesas_mensais * 6
reserva_atual = perfil['reserva_emergencia_atual']
progresso_reserva = (reserva_atual / reserva_ideal) * 100
meses_cobertos = reserva_atual / despesas_mensais

# Análise de categorias para orientação de economia
categorias_gastos = transacoes[transacoes['tipo'] == 'saida'].groupby('categoria')['valor'].sum().sort_values(ascending=False)

contexto = f"""
CLIENTE: {perfil['nome']}, {perfil['idade']} anos, perfil {perfil['perfil_investidor']}
OBJETIVO: {perfil['objetivo_principal']}
PATRIMÔNIO: R$ {perfil['patrimonio_total']:,} | RESERVA ATUAL: R$ {reserva_atual:,}

ANÁLISE DE RESERVA DE EMERGÊNCIA:
- Despesas mensais totais: R$ {despesas_mensais:,.2f}
- Reserva ideal (6 meses): R$ {reserva_ideal:,.2f}
- Progresso atual: {progresso_reserva:.1f}% ({meses_cobertos:.1f} meses cobertos)
- Valor restante para completar: R$ {reserva_ideal - reserva_atual:,.2f}

ANÁLISE DE GASTOS POR CATEGORIA (para orientação de economia):
{categorias_gastos.to_string()}

TRANSAÇÕES RECENTES:
{transacoes.to_string(index=False)}

ATENDIMENTOS ANTERIORES:
{historico.to_string(index=False)}

PRODUTOS DISPONÍVEIS:
{json.dumps(produtos, indent=2, ensure_ascii=False)}
"""

# ============ SYSTEM PROMPT ============
SYSTEM_PROMPT = """Você é o POFI (Profissional de Finanças Inteligente), um assistente financeiro amigável e didático.

OBJETIVO PRINCIPAL:
Orientar o usuário sobre como guardar dinheiro para emergências e ensinar economia de dinheiro de forma segura e eficiente.

REGRAS:
- NUNCA recomende investimentos específicos, apenas explique como funcionam;
- JAMAIS responda a perguntas fora do tema ensino de finanças pessoais. 
  Quando ocorrer, responda lembrando o seu papel de assistente financeiro;
- Use os dados fornecidos para dar exemplos personalizados sobre reserva de emergência e economia;
- Linguagem simples, como se explicasse para um amigo;
- Se não souber algo, admita: "Não tenho essa informação, mas posso explicar...";
- Sempre pergunte se o cliente entendeu;
- Responda de forma sucinta e direta, com no máximo 3 parágrafos;
- FOCO ESPECIAL: Reserve de emergência = 6 meses de despesas fixas;
- Calcule e mostre o progresso atual do usuário em relação à meta ideal;
- ORIENTE SOBRE ECONOMIA: Sugira estratégias para reduzir gastos baseados nas categorias de despesas do cliente.
"""

# ============ CHAMAR OLLAMA ============
def perguntar(msg):
    prompt = f"""
    {SYSTEM_PROMPT}

    CONTEXTO DO CLIENTE:
    {contexto}

    Pergunta: {msg}"""

    r = requests.post(OLLAMA_URL, json={"model": MODELO, "prompt": prompt, "stream": False})
    return r.json()['response']

# ============ INTERFACE ============
st.title("🎓 POFI - Profissional de Finanças Inteligente")

# Mostrar dashboard da reserva de emergência
st.markdown("### 📊 Situação Atual da Reserva de Emergência")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Despesas Mensais", f"R$ {despesas_mensais:,.2f}")
with col2:
    st.metric("Reserva Ideal", f"R$ {reserva_ideal:,.2f}")
with col3:
    st.metric("Progresso", f"{progresso_reserva:.1f}%")
with col4:
    st.metric("Meses Cobertos", f"{meses_cobertos:.1f}")

# Barra de progresso
st.progress(progresso_reserva / 100)
st.markdown(f"*Você já tem **{meses_cobertos:.1f} meses** de despesas cobertas. Faltam **{6 - meses_cobertos:.1f} meses** para atingir a meta ideal!*")

st.markdown("---")

if pergunta := st.chat_input("Sua dúvida sobre finanças..."):
    st.chat_message("user").write(pergunta)
    with st.spinner("..."):
        st.chat_message("assistant").write(perguntar(pergunta))
