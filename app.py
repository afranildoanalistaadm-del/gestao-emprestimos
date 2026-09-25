import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Sistema de Gestão de Empréstimos", page_icon="📊", layout="wide")

if 'clientes' not in st.session_state:
    st.session_state.clientes = []
if 'contratos' not in st.session_state:
    st.session_state.contratos = []
if 'pagamentos' not in st.session_state:
    st.session_state.pagamentos = []

st.sidebar.title("Navegação")
menu = st.sidebar.selectbox("Ir para", ["Dashboard", "Novo Cliente", "Novo Contrato", "Registrar Pagamento", "Auditoria & Relatórios"])

st.sidebar.markdown("---")
st.sidebar.subheader("Painel de Sessão")
if st.sidebar.button("💾 Salvar dados"):
    st.sidebar.success("Dados salvos na sessão com sucesso!")
if st.sidebar.button("🚪 Sair / Encerrar"):
    st.sidebar.warning("Sessão encerrada (limpeza simulada).")
    st.session_state.clientes = []
    st.session_state.contratos = []
    st.session_state.pagamentos = []
    st.rerun()

# ----------------------------------------------------
# 1. DASHBOARD
# ----------------------------------------------------
if menu == "Dashboard":
    st.title("📊 Sistema de Gestão de Empréstimos (MVP)")
    st.markdown("Painel limpo para controle de carteira, contratos, amortizações e auditoria.")
    
    if not st.session_state.contratos:
        st.info("Nenhum contrato cadastrado ainda. Vá em 'Novo Contrato' para começar.")
    else:
        total_emprestado = sum(c['Valor_Original'] for c in st.session_state.contratos)
        total_pago = sum(p['Valor_Pago'] for p in st.session_state.pagamentos)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Emprestado", f"R$ {total_emprestado:,.2f}")
        col2.metric("Total Recebido", f"R$ {total_pago:,.2f}")
        col3.metric("Contratos Ativos", len(st.session_state.contratos))
        
        st.subheader("Resumo da Carteira")
        df_c = pd.DataFrame(st.session_state.contratos)
        st.dataframe(df_c, use_container_width=True)

# ----------------------------------------------------
# 2. NOVO CLIENTE (Exclusão limpa e sincronizada)
# ----------------------------------------------------
elif menu == "Novo Cliente":
    st.title("👤 Cadastro e Gestão de Clientes")
    st.markdown("Painel para cadastrar e gerenciar clientes.")
    
    col_esq, col_dir = st.columns(2)
    
    with col_esq:
        st.subheader("Novo Cliente")
        with st.form("form_cliente"):
            nome = st.text_input("Nome ou Razão Social")
            telefone = st.text_input("Telefone / Contato")
            doc = st.text_input("CPF ou CNPJ")
            submit = st.form_submit_button("Salvar Cliente")
            
            if submit:
                if nome:
                    novo_id = len(st.session_state.clientes) + 1
                    st.session_state.clientes.append({"ID": novo_id, "Nome": nome, "Contato": telefone, "Documento": doc})
                    st.success(f"Cliente '{nome}' cadastrado com sucesso!")
                else:
                    st.error("O campo Nome é obrigatório.")
                    
    with col_dir:
        st.subheader("🗑️ Excluir Cliente")
        if not st.session_state.clientes:
            st.info("Nenhum cliente cadastrado.")
        else:
            cli_nomes_del = {c['Nome']: c for c in st.session_state.clientes}
            cli_sel_del = st.selectbox("Selecione o cliente para excluir", list(cli_nomes_del.keys()), key="del_cli")
            obj_del = cli_nomes_del[cli_sel_del]
            
            contratos_vinculados = [c for c in st.session_state.contratos if c['Cliente'] == obj_del['Nome']]
            
            if contratos_vinculados:
                st.warning(f"Atenção: Este cliente possui {len(contratos_vinculados)} contrato(s) e histórico vinculado(s).")
            
            if st.button("Excluir Cliente e Registros Vinculados", type="primary"):
                # IDs dos contratos deste cliente
                ids_contratos_remover = [c['ID'] for c in contratos_vinculados]
                
                # Remove o cliente
                st.session_state.clientes = [c for c in st.session_state.clientes if c['ID'] != obj_del['ID']]
                # Remove os contratos do cliente
                st.session_state.contratos = [c for c in st.session_state.contratos if c['Cliente'] != obj_del['Nome']]
                # Remove os pagamentos associados a esses contratos
                st.session_state.pagamentos = [p for p in st.session_state.pagamentos if p['Contrato_ID'] not in ids_contratos_remover]
                
                st.success("Cliente e todos os registros associados excluídos com sucesso!")
                st.rerun()

    st.markdown("---")
    st.subheader("Clientes Cadastrados na Base")
    if st.session_state.clientes:
        st.dataframe(pd.DataFrame(st.session_state.clientes), use_container_width=True)
    else:
        st.info("Nenhum cliente na base.")

# ----------------------------------------------------
# 3. NOVO CONTRATO
# ----------------------------------------------------
elif menu == "Novo Contrato":
    st.title("📄 Novo Contrato de Empréstimo")
    
    if not st.session_state.clientes:
        st.warning("Cadastre pelo menos um cliente antes de criar um contrato.")
    else:
        clientes_lista = [c['Nome'] for c in st.session_state.clientes]
        with st.form("form_contrato"):
            cli = st.selectbox("Cliente", clientes_lista)
            valor_emp = st.number_input("Valor do Empréstimo Principal (R$)", min_value=0.0, format="%.2f")
            num_parcelas = st.slider("Número de Parcelas", min_value=1, max_value=24, value=10)
            taxa_normal = st.number_input("Taxa Normal (% ao mês)", min_value=0.0, value=15.0, format="%.2f")
            taxa_atraso = st.number_input("Taxa de Atraso (% ao mês)", min_value=0.0, value=2.0, format="%.2f")
            data_venc = st.text_input("Data de Vencimento da 1ª Parcela (Formato: DD/MM/AAAA)", value="25/10/2026")
            
            submit_c = st.form_submit_button("Criar Contrato")
            if submit_c:
                if valor_emp > 0:
                    novo_id_c = len(st.session_state.contratos) + 1
                    # Aplicação da taxa normal sobre o principal inicial (Ex: 500 + 15% = 575)
                    saldo_inicial = valor_emp * (1 + (taxa_normal / 100))
                    st.session_state.contratos.append({
                        "ID": novo_id_c,
                        "Cliente": cli,
                        "Valor_Original": valor_emp,
                        "Parcela_Atual": 0,
                        "Total_Parcelas": num_parcelas,
                        "Taxa_Normal": taxa_normal,
                        "Taxa_Atraso": taxa_atraso,
                        "Data_Vencimento": data_venc,
                        "Saldo_Atual": saldo_inicial,
                        "Status": "Em dia",
                        "Dias_Atraso": 0,
                        "Parcelas": f"0 de {num_parcelas}"
                    })
                    st.success(f"Contrato criado com sucesso! Status inicial: 0 de {num_parcelas} | Saldo Inicial: R$ {saldo_inicial:,.2f}")
                else:
                    st.error("O valor do empréstimo deve ser maior que zero.")
                    
        st.subheader("Contratos na Base")
        if st.session_state.contratos:
            st.dataframe(pd.DataFrame(st.session_state.contratos), use_container_width=True)

# ----------------------------------------------------
# 4. REGISTRAR PAGAMENTO
# ----------------------------------------------------
elif menu == "Registrar Pagamento":
    st.title("💰 Registrar Pagamento / Amortização")
    
    if not st.session_state.contratos:
        st.info("Nenhum contrato ativo para registrar pagamentos.")
    else:
        contratos_opcoes = {f"Contrato #{c['ID']} - {c['Cliente']} (Pagas: {c['Parcela_Atual']} de {c['Total_Parcelas']} | Saldo Devedor: R$ {c['Saldo_Atual']:,.2f})": c for c in st.session_state.contratos}
        
        with st.form("form_pagamento"):
            sel_str = st.selectbox("Selecione o Contrato", list(contratos_opcoes.keys()))
            contrato_obj = contratos_opcoes[sel_str]
            
            valor_pag = st.number_input("Valor Pago pelo Cliente (R$)", min_value=0.0, format="%.2f")
            dias_atraso_input = st.number_input("Dias de Atraso (se houver)", min_value=0, value=0, step=1)
            data_pag = st.text_input("Data do Pagamento (Formato: DD/MM/AAAA)", value="25/09/2026")
            
            submit_p = st.form_submit_button("Confirmar Amortização e Avançar Parcela")
            if submit_p:
                if valor_pag > 0:
                    novo_id_p = len(st.session_state.pagamentos) + 1
                    
                    # 1. Saldo atual antes do pagamento, acrescido de juros diários de atraso se houver
                    saldo_devedor_atual = contrato_obj['Saldo_Atual']
                    taxa_atraso_mensal = contrato_obj['Taxa_Atraso']
                    
                    juros_atraso_total = 0.0
                    if dias_atraso_input > 0:
                        taxa_atraso_diaria = (taxa_atraso_mensal / 100) / 30.0
                        juros_atraso_total = saldo_devedor_atual * taxa_atraso_diaria * dias_atraso_input
                        saldo_devedor_atual += juros_atraso_total
                    
                    # 2. Subtrai o valor pago pelo cliente
                    restante_apos_pagamento = max(0.0, saldo_devedor_atual - valor_pag)
                    
                    # 3. Aplica a taxa normal (% ao mês) sobre o saldo restante (Ex: 375 + 15% = 431.25)
                    taxa_normal_mensal = contrato_obj['Taxa_Normal']
                    novo_saldo = restante_apos_pagamento * (1 + (taxa_normal_mensal / 100))
                    
                    # Atualiza o contrato na sessão
                    for c in st.session_state.contratos:
                        if c['ID'] == contrato_obj['ID']:
                            c['Parcela_Atual'] = min(c['Total_Parcelas'], c['Parcela_Atual'] + 1)
                            c['Saldo_Atual'] = novo_saldo
                            c['Dias_Atraso'] = dias_atraso_input
                            c['Status'] = "Em atraso" if dias_atraso_input > 0 else "Em dia"
                            c['Parcelas'] = f"{c['Parcela_Atual']} de {c['Total_Parcelas']}"
                    
                    st.session_state.pagamentos.append({
                        "ID": novo_id_p,
                        "Contrato_ID": contrato_obj['ID'],
                        "Cliente": contrato_obj['Cliente'],
                        "Valor_Pago": valor_pag,
                        "Dias_Atraso": dias_atraso_input,
                        "Juros_Atraso": juros_atraso_total,
                        "Data_Pagamento": data_pag,
                        "Novo_Saldo": novo_saldo
                    })
                    st.success(f"Pagamento registrado com sucesso! Restante após abatimento com juros normais: R$ {novo_saldo:,.2f}")
                    st.rerun()
                else:
                    st.error("O valor do pagamento deve ser maior que zero.")
                    
        st.subheader("Histórico de Pagamentos e Correção de Lançamentos")
        if st.session_state.pagamentos:
            df_p = pd.DataFrame(st.session_state.pagamentos)
            st.dataframe(df_p, use_container_width=True)
            
            st.markdown("### 🗑️ Excluir / Reverter Pagamento Incorreto")
            pag_ids = [p['ID'] for p in st.session_state.pagamentos]
            del_pag_id = st.selectbox("Selecione o ID do Pagamento para Excluir", pag_ids)
            if st.button("Excluir Pagamento Selecionado", type="primary"):
                st.session_state.pagamentos = [p for p in st.session_state.pagamentos if p['ID'] != del_pag_id]
                st.success("Pagamento excluído com sucesso!")
                st.rerun()

# ----------------------------------------------------
# 5. AUDITORIA & RELATÓRIOS
# ----------------------------------------------------
elif menu == "Auditoria & Relatórios":
    st.title("📋 Relatório de Auditoria para Conferência")
    st.markdown("Consolidado completo de todas as movimentações e contratos para prestação de contas e auditoria.")
    
    st.subheader("1. Auditoria de Contratos")
    if st.session_state.contratos:
        st.dataframe(pd.DataFrame(st.session_state.contratos), use_container_width=True)
    else:
        st.info("Nenhum contrato cadastrado.")
        
    st.subheader("2. Auditoria de Pagamentos Realizados")
    if st.session_state.pagamentos:
        df_aud_pag = pd.DataFrame(st.session_state.pagamentos)
        st.dataframe(df_aud_pag, use_container_width=True)
        csv_data = df_aud_pag.to_csv(index=False).encode('utf-8')
        st.download_button("Baixar Relatório de Contratos (CSV para Auditoria)", csv_data, "relatorio_auditoria.csv", "text/csv")
    else:
        st.info("Nenhum pagamento registrado.")
