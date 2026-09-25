import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Gestão de Empréstimos", page_icon="📊", layout="wide")

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
        total_emprestado = sum(c['Valor'] for c in st.session_state.contratos)
        total_pago = sum(p['Valor'] for p in st.session_state.pagamentos)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Emprestado", f"R$ {total_emprestado:,.2f}")
        col2.metric("Total Recebido", f"R$ {total_pago:,.2f}")
        col3.metric("Contratos Ativos", len(st.session_state.contratos))
        
        st.subheader("Resumo da Carteira")
        df_c = pd.DataFrame(st.session_state.contratos)
        st.dataframe(df_c, use_container_width=True)

# ----------------------------------------------------
# 2. NOVO CLIENTE (Com Abas: Cadastrar, Editar e Excluir)
# ----------------------------------------------------
elif menu == "Novo Cliente":
    st.title("👤 Gestão de Clientes")
    
    tab1, tab2, tab3 = st.tabs(["Cadastrar Cliente", "Editar Cliente", "Excluir Cliente"])
    
    with tab1:
        st.subheader("Cadastrar Novo Cliente")
        with st.form("form_cliente"):
            nome = st.text_input("Nome ou Razão Social *")
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
                    
    with tab2:
        st.subheader("Editar Dados do Cliente")
        if not st.session_state.clientes:
            st.info("Nenhum cliente cadastrado para editar.")
        else:
            cliente_nomes = {c['Nome']: c for c in st.session_state.clientes}
            selecionado_ed = st.selectbox("Selecione o cliente para editar", list(cliente_nomes.keys()), key="edit_cli")
            cli_obj = cliente_nomes[selecionado_ed]
            
            with st.form("form_edit_cliente"):
                novo_nome = st.text_input("Nome ou Razão Social", value=cli_obj['Nome'])
                novo_tel = st.text_input("Telefone / Contato", value=cli_obj['Contato'])
                novo_doc = st.text_input("CPF ou CNPJ", value=cli_obj['Documento'])
                btn_salvar_ed = st.form_submit_button("Salvar Alterações")
                
                if btn_salvar_ed:
                    cli_obj['Nome'] = novo_nome
                    cli_obj['Contato'] = novo_tel
                    cli_obj['Documento'] = novo_doc
                    st.success("Dados do cliente atualizados com sucesso!")
                    st.rerun()

    with tab3:
        st.subheader("Excluir Cliente")
        if not st.session_state.clientes:
            st.info("Nenhum cliente cadastrado.")
        else:
            cli_nomes_del = {c['Nome']: c for c in st.session_state.clientes}
            cli_sel_del = st.selectbox("Selecione o cliente para excluir", list(cli_nomes_del.keys()), key="del_cli")
            obj_del = cli_nomes_del[cli_sel_del]
            
            contratos_vinculados = [c for c in st.session_state.contratos if c['Cliente'] == obj_del['Nome']]
            
            if contratos_vinculados:
                st.warning(f"Não é possível excluir o cliente '{obj_del['Nome']}' pois existem {len(contratos_vinculados)} contratos vinculados a ele.")
                for_car = st.checkbox("Forçar exclusão (Isso também removerá os contratos vinculados)")
                if st.button("Excluir Cliente e Contratos Vinculados", type="primary"):
                    if for_car:
                        st.session_state.contratos = [c for c in st.session_state.contratos if c['Cliente'] != obj_del['Nome']]
                        st.session_state.clientes = [c for c in st.session_state.clientes if c['ID'] != obj_del['ID']]
                        st.success("Cliente e vínculos removidos com sucesso!")
                        st.rerun()
                    else:
                        st.error("Marque a caixa de confirmação para forçar a exclusão.")
            else:
                if st.button("Excluir Cliente Selecionado", type="primary"):
                    st.session_state.clientes = [c for c in st.session_state.clientes if c['ID'] != obj_del['ID']]
                    st.success("Cliente excluído com sucesso!")
                    st.rerun()

    st.markdown("---")
    st.subheader("Clientes Cadastrados na Base")
    if st.session_state.clientes:
        st.dataframe(pd.DataFrame(st.session_state.clientes), use_container_width=True)
    else:
        st.info("Nenhum cliente na base.")

# ----------------------------------------------------
# 3. NOVO CONTRATO (Padrão Original Exato)
# ----------------------------------------------------
elif menu == "Novo Contrato":
    st.title("📄 Cadastro de Contrato de Empréstimo")
    
    if not st.session_state.clientes:
        st.warning("Cadastre pelo menos um cliente antes de criar um contrato.")
    else:
        clientes_lista = [c['Nome'] for c in st.session_state.clientes]
        with st.form("form_contrato"):
            cli = st.selectbox("Cliente", clientes_lista)
            valor_emp = st.number_input("Valor do Empréstimo (R$)", min_value=0.0, format="%.2f")
            taxa_juros = st.number_input("Taxa de Juros (%)", min_value=0.0, format="%.2f")
            data_emp = st.date_input("Data do Contrato", value=datetime.today())
            
            submit_c = st.form_submit_button("Criar Contrato")
            if submit_c:
                if valor_emp > 0:
                    novo_id_c = len(st.session_state.contratos) + 1
                    st.session_state.contratos.append({
                        "ID": novo_id_c,
                        "Cliente": cli,
                        "Valor": valor_emp,
                        "Taxa (%)": taxa_juros,
                        "Data": str(data_emp)
                    })
                    st.success(f"Contrato #{novo_id_c} criado para {cli} com taxa de {taxa_juros}%!")
                else:
                    st.error("O valor do empréstimo deve ser maior que zero.")
                    
        st.subheader("Contratos Ativos")
        if st.session_state.contratos:
            st.dataframe(pd.DataFrame(st.session_state.contratos), use_container_width=True)

# ----------------------------------------------------
# 4. REGISTRAR PAGAMENTO
# ----------------------------------------------------
elif menu == "Registrar Pagamento":
    st.title("💰 Registro de Pagamento / Amortização")
    
    if not st.session_state.contratos:
        st.info("Nenhum contrato ativo para registrar pagamentos.")
    else:
        contratos_ids = [c['ID'] for c in st.session_state.contratos]
        with st.form("form_pagamento"):
            id_contrato = st.selectbox("ID do Contrato", contratos_ids)
            valor_pag = st.number_input("Valor Pago (R$)", min_value=0.0, format="%.2f")
            data_pag = st.date_input("Data do Pagamento", value=datetime.today())
            
            submit_p = st.form_submit_button("Registrar Pagamento")
            if submit_p:
                if valor_pag > 0:
                    st.session_state.pagamentos.append({
                        "ID Contrato": id_contrato,
                        "Valor": valor_pag,
                        "Data": str(data_pag)
                    })
                    st.success(f"Pagamento de R$ {valor_pag:,.2f} registrado no Contrato #{id_contrato}!")
                else:
                    st.error("O valor do pagamento deve ser maior que zero.")
                    
        st.subheader("Histórico de Pagamentos")
        if st.session_state.pagamentos:
            st.dataframe(pd.DataFrame(st.session_state.pagamentos), use_container_width=True)

# ----------------------------------------------------
# 5. AUDITORIA & RELATÓRIOS
# ----------------------------------------------------
elif menu == "Auditoria & Relatórios":
    st.title("🔍 Painel de Auditoria e Relatórios")
    
    st.subheader("Exportar Dados em CSV")
    if st.session_state.contratos:
        df_contratos = pd.DataFrame(st.session_state.contratos)
        st.download_button("Baixar Contratos (CSV)", df_contratos.to_csv(index=False).encode('utf-8'), "contratos.csv", "text/csv")
    
    if st.session_state.pagamentos:
        df_pagamentos = pd.DataFrame(st.session_state.pagamentos)
        st.download_button("Baixar Pagamentos (CSV)", df_pagamentos.to_csv(index=False).encode('utf-8'), "pagamentos.csv", "text/csv")
        
    st.markdown("---")
    st.subheader("Auditoria Geral do Sistema")
    st.write(f"Total de Clientes cadastrados: {len(st.session_state.clientes)}")
    st.write(f"Total de Contratos criados: {len(st.session_state.contratos)}")
    st.write(f"Total de Pagamentos registrados: {len(st.session_state.pagamentos)}")
       
