from datetime import datetime, date, timedelta
import pandas as pd
import streamlit as st

# Configuração da página
st.set_page_config(page_title="MVP - Gestão de Empréstimos", page_icon="💰", layout="wide")

# Inicializadora do Banco de Dados em Memória (Session State) para o MVP
if 'clientes' not in st.session_state:
    st.session_state.clientes = pd.DataFrame(columns=["ID", "Nome", "Contato", "Documento"])

if 'contratos' not in st.session_state:
    st.session_state.contratos = pd.DataFrame(columns=[
        "ID", "Cliente", "Valor_Original", "Parcela_Atual", "Total_Parcelas", "Taxa_Normal", 
        "Taxa_Atraso", "Data_Vencimento", "Saldo_Atual", "Status", "Dias_Atraso"
    ])

if 'pagamentos' not in st.session_state:
    st.session_state.pagamentos = pd.DataFrame(columns=[
        "ID", "Contrato_ID", "Cliente", "Valor_Pago", "Data_Pagamento", "Novo_Saldo"
    ])

# Função de atualização automática de juros e atrasos baseada na data atual
def atualizar_status_e_juros():
    if st.session_state.contratos.empty:
        return
    
    hoje = date.today()
    
    for idx, row in st.session_state.contratos.iterrows():
        if row["Status"] == "Quitado":
            continue
            
        try:
            venc_obj = datetime.strptime(str(row["Data_Vencimento"]), '%d/%m/%Y').date()
        except ValueError:
            continue
            
        saldo = float(row["Saldo_Atual"])
        taxa_atraso_diaria = (float(row["Taxa_Atraso"]) / 100.0) / 30.0 
        
        if hoje > venc_obj:
            dias_atraso = (hoje - venc_obj).days
            juros_atraso = saldo * (taxa_atraso_diaria * 1) 
            novo_saldo = saldo + juros_atraso
            
            st.session_state.contratos.at[idx, "Saldo_Atual"] = round(novo_saldo, 2)
            st.session_state.contratos.at[idx, "Status"] = "Em atraso"
            st.session_state.contratos.at[idx, "Dias_Atraso"] = dias_atraso
        else:
            st.session_state.contratos.at[idx, "Status"] = "Em dia"
            st.session_state.contratos.at[idx, "Dias_Atraso"] = 0

# Executa a verificação
atualizar_status_e_juros()

# Título Principal
st.title("📊 Sistema de Gestão de Empréstimos (MVP)")
st.markdown("Painel limpo para controle de carteira, contratos, amortizações e auditoria.")

# ==========================================
# MENU LATERAL E PAINEL DE CONTROLE
# ==========================================
st.sidebar.title("Navegação")
menu = st.sidebar.selectbox("Ir para", ["Dashboard", "Cadastrar Cliente", "Novo Contrato", "Registrar Pagamento", "Relatório de Auditoria"])

st.sidebar.markdown("---")
st.sidebar.subheader("Painel de Sessão")

if st.sidebar.button("💾 Salvar dados", use_container_width=True):
    st.sidebar.success("Dados salvos na sessão com sucesso!")

if st.sidebar.button("🚪 Sair / Encerrar", use_container_width=True):
    st.sidebar.warning("Sessão encerrada.")

# ==========================================
# 1. DASHBOARD PRINCIPAL
# ==========================================
if menu == "Dashboard":
    st.header("Visão Geral da Carteira")
    
    if st.session_state.contratos.empty:
        st.info("Nenhum contrato cadastrado ainda. Vá em 'Novo Contrato' para começar.")
    else:
        st.subheader("🔍 Filtros Avançados")
        col_f1, col_f2 = st.columns(2)
        status_filter = col_f1.selectbox("Filtrar por Status", ["Todos", "Em dia", "Em atraso", "Quitado"])
        cliente_filter = col_f2.selectbox("Filtrar por Cliente", ["Todos"] + st.session_state.contratos["Cliente"].unique().tolist())
        
        df_view = st.session_state.contratos.copy()
        if status_filter != "Todos":
            df_view = df_view[df_view["Status"] == status_filter]
        if cliente_filter != "Todos":
            df_view = df_view[df_view["Cliente"] == cliente_filter]

        col1, col2, col3, col4 = st.columns(4)
        capital_total = st.session_state.contratos["Valor_Original"].sum()
        saldo_devedor = df_view["Saldo_Atual"].sum()
        contratos_atrasados = df_view[df_view["Status"] == "Em atraso"]
        valor_em_atraso = contratos_atrasados["Saldo_Atual"].sum()
        taxa_inadimplencia = (valor_em_atraso / saldo_devedor * 100) if saldo_devedor > 0 else 0
        
        col1.metric(label="Capital Emprestado", value=f"R$ {capital_total:,.2f}")
        col2.metric(label="Saldo Devedor Atualizado", value=f"R$ {saldo_devedor:,.2f}")
        col3.metric(label="Valor em Atraso", value=f"R$ {valor_em_atraso:,.2f}")
        col4.metric(
            label="Inadimplência da Carteira", 
            value=f"{taxa_inadimplencia:.1f}%",
            delta="Alerta Crítico" if taxa_inadimplencia > 10 else "Normal",
            delta_color="inverse"
        )
        
        st.markdown("---")
        st.subheader("Relação de Contratos Ativos")
        
        df_exibicao = df_view.copy()
        if "Parcela_Atual" in df_exibicao.columns and "Total_Parcelas" in df_exibicao.columns:
            df_exibicao["Parcelas"] = df_exibicao["Parcela_Atual"].astype(str) + " de " + df_exibicao["Total_Parcelas"].astype(str)
            cols = ["ID", "Cliente", "Valor_Original", "Parcelas", "Taxa_Normal", "Taxa_Atraso", "Data_Vencimento", "Saldo_Atual", "Status", "Dias_Atraso"]
            df_exibicao = df_exibicao[[c for c in cols if c in df_exibicao.columns]]
            
        st.dataframe(df_exibicao, use_container_width=True)

# ==========================================
# 2. CADASTRO E EXCLUSÃO DE CLIENTES
# ==========================================
elif menu == "Cadastrar Cliente":
    st.header("👤 Cadastro e Gestão de Clientes")
    
    col_cad, col_del = st.columns(2)
    
    with col_cad:
        st.subheader("Novo Cliente")
        with st.form("form_cliente"):
            nome = st.text_input("Nome ou Razão Social")
            contato = st.text_input("Telefone / Contato")
            documento = st.text_input("CPF ou CNPJ")
            submitted = st.form_submit_button("Salvar Cliente")
            
            if submitted and nome:
                novo_id = int(st.session_state.clientes["ID"].max() + 1) if not st.session_state.clientes.empty else 1
                novo_cliente = pd.DataFrame([[novo_id, nome, contato, documento]], columns=["ID", "Nome", "Contato", "Documento"])
                st.session_state.clientes = pd.concat([st.session_state.clientes, novo_cliente], ignore_index=True)
                st.success(f"Cliente '{nome}' cadastrado com sucesso!")
                st.rerun()
            elif submitted:
                st.error("O campo Nome é obrigatório.")
                
    with col_del:
        st.subheader("🗑️ Excluir Cliente")
        if st.session_state.clientes.empty:
            st.info("Nenhum cliente cadastrado para exclusão.")
        else:
            cliente_para_excluir = st.selectbox("Selecione o cliente para excluir", st.session_state.clientes["Nome"].tolist())
            btn_excluir = st.button("Excluir Cliente Selecionado", type="primary")
            
            if btn_excluir:
                tem_contrato = not st.session_state.contratos[st.session_state.contratos["Cliente"] == cliente_para_excluir].empty
                if tem_contrato:
                    st.error("Não é possível excluir este cliente pois existem contratos vinculados a ele.")
                else:
                    st.session_state.clientes = st.session_state.clientes[st.session_state.clientes["Nome"] != cliente_para_excluir]
                    st.success(f"Cliente '{cliente_para_excluir}' excluído com sucesso!")
                    st.rerun()
            
    st.markdown("---")
    st.subheader("Clientes Cadastrados na Base")
    st.dataframe(st.session_state.clientes, use_container_width=True)

# ==========================================
# 3. NOVO CONTRATO
# ==========================================
elif menu == "Novo Contrato":
    st.header("📄 Novo Contrato de Empréstimo")
    
    if st.session_state.clientes.empty:
        st.warning("Cadastre pelo menos um cliente antes de criar um contrato.")
    else:
        clientes_lista = st.session_state.clientes["Nome"].tolist()
        data_sugestao = (date.today() + timedelta(days=30)).strftime('%d/%m/%Y')
        
        with st.form("form_contrato"):
            cliente_selecionado = st.selectbox("Cliente", clientes_lista)
            valor_original = st.number_input("Valor do Empréstimo Principal (R$)", min_value=0.0, step=100.0)
            parcelas = st.slider("Número de Parcelas", min_value=1, max_value=24, value=10)
            
            col_t1, col_t2 = st.columns(2)
            taxa_normal = col_t1.number_input("Taxa Normal (% ao mês)", value=15.0, step=0.5)
            taxa_atraso = col_t2.number_input("Taxa de Atraso (% ao mês)", value=2.0, step=0.5)
            
            data_vencimento_str = st.text_input(
                "Data de Vencimento da 1ª Parcela (Formato: DD/MM/AAAA)",
                value=data_sugestao,
                max_chars=10
            )
            
            submitted_contrato = st.form_submit_button("Criar Contrato")
            
            if submitted_contrato and valor_original > 0:
                try:
                    data_obj = datetime.strptime(data_vencimento_str.strip(), '%d/%m/%Y')
                    data_formatada_banco = data_obj.strftime('%d/%m/%Y')
                except ValueError:
                    st.error("Formato de data inválido! Utilize DD/MM/AAAA.")
                    st.stop()
                
                juros_iniciais = valor_original * (taxa_normal / 100.0)
                saldo_inicial = valor_original + juros_iniciais
                
                novo_id_c = int(st.session_state.contratos["ID"].max() + 1) if not st.session_state.contratos.empty else 1
                novo_contrato = pd.DataFrame([[
                    novo_id_c,
                    cliente_selecionado,
                    valor_original,
                    0, 
                    int(parcelas), 
                    taxa_normal,
                    taxa_atraso,
                    data_formatada_banco,
                    round(saldo_inicial, 2),
                    "Em dia",
                    0
                ]], columns=[
                    "ID", "Cliente", "Valor_Original", "Parcela_Atual", "Total_Parcelas", "Taxa_Normal", 
                    "Taxa_Atraso", "Data_Vencimento", "Saldo_Atual", "Status", "Dias_Atraso"
                ])
                st.session_state.contratos = pd.concat([st.session_state.contratos, novo_contrato], ignore_index=True)
                st.success(f"Contrato criado com sucesso! Status inicial: 0 de {parcelas} | Saldo Inicial: R$ {saldo_inicial:,.2f}")
            elif submitted_contrato:
                st.error("Informe um valor de empréstimo válido.")
                
    st.subheader("Contratos na Base")
    df_base = st.session_state.contratos.copy()
    if not df_base.empty and "Parcela_Atual" in df_base.columns:
        df_base["Parcelas"] = df_base["Parcela_Atual"].astype(str) + " de " + df_base["Total_Parcelas"].astype(str)
    st.dataframe(df_base, use_container_width=True)

# ==========================================
# 4. REGISTRAR PAGAMENTO
# ==========================================
elif menu == "Registrar Pagamento":
    st.header("💸 Registrar Pagamento / Amortização")
    
    contratos_ativos = st.session_state.contratos[st.session_state.contratos["Status"] != "Quitado"]
    
    if contratos_ativos.empty:
        st.info("Não há contratos ativos pendentes de pagamento.")
    else:
        contratos_ativos["Label_Select"] = (
            "Contrato #" + contratos_ativos["ID"].astype(str) + 
            " - " + contratos_ativos["Cliente"] + 
            " (Pagas: " + contratos_ativos["Parcela_Atual"].astype(str) + " de " + contratos_ativos["Total_Parcelas"].astype(str) + 
            " | Saldo Devedor: R$ " + contratos_ativos["Saldo_Atual"].astype(str) + ")"
        )
        
        data_pag_sugestao = date.today().strftime('%d/%m/%Y')
        
        with st.form("form_pagamento"):
            contrato_escolhido = st.selectbox("Selecione o Contrato", contratos_ativos["Label_Select"])
            valor_pago = st.number_input("Valor Pago pelo Cliente (R$)", min_value=0.0, step=50.0)
            data_pagamento_str = st.text_input("Data do Pagamento (Formato: DD/MM/AAAA)", value=data_pag_sugestao, max_chars=10)
            
            submitted_pag = st.form_submit_button("Confirmar Amortização e Avançar Parcela")
            
            if submitted_pag and valor_pago > 0:
                try:
                    data_pag_obj = datetime.strptime(data_pagamento_str.strip(), '%d/%m/%Y')
                    data_pag_formatada = data_pag_obj.strftime('%d/%m/%Y')
                except ValueError:
                    st.error("Formato de data inválido! Utilize DD/MM/AAAA.")
                    st.stop()
                
                id_contrato = int(contrato_escolhido.split(" ")[1].replace("#", ""))
                idx = st.session_state.contratos[st.session_state.contratos["ID"] == id_contrato].index[0]
                contrato = st.session_state.contratos.loc[idx]
                
                saldo_atual = float(contrato["Saldo_Atual"])
                taxa_normal = float(contrato["Taxa_Normal"]) / 100.0
                parcela_atual = int(contrato["Parcela_Atual"])
                total_parcelas = int(contrato["Total_Parcelas"])
                
                # Cálculo correto: (Saldo - Valor Pago) + Juros sobre o restante
                saldo_apos_abatimento = saldo_atual - valor_pago
                nova_parcela = parcela_atual + 1
                
                if saldo_apos_abatimento <= 0 or nova_parcela > total_parcelas:
                    novo_saldo = 0.0
                    novo_status = "Quitado"
                    nova_parcela = total_parcelas
                else:
                    novo_saldo = saldo_apos_abatimento + (saldo_apos_abatimento * taxa_normal)
                    novo_status = "Em dia"
                
                st.session_state.contratos.at[idx, "Saldo_Atual"] = round(novo_saldo, 2)
                st.session_state.contratos.at[idx, "Parcela_Atual"] = nova_parcela
                st.session_state.contratos.at[idx, "Status"] = novo_status
                st.session_state.contratos.at[idx, "Dias_Atraso"] = 0
                
                novo_pag_id = int(st.session_state.pagamentos["ID"].max() + 1) if not st.session_state.pagamentos.empty else 1
                novo_pag = pd.DataFrame([[
                    novo_pag_id,
                    id_contrato,
                    contrato["Cliente"],
                    valor_pago,
                    data_pag_formatada,
                    round(novo_saldo, 2)
                ]], columns=["ID", "Contrato_ID", "Cliente", "Valor_Pago", "Data_Pagamento", "Novo_Saldo"])
                
                st.session_state.pagamentos = pd.concat([st.session_state.pagamentos, novo_pag], ignore_index=True)
                st.success(f"Pagamento registrado! Parcelas pagas atualizada para **{nova_parcela} de {total_parcelas}** | Novo saldo: R$ {novo_saldo:,.2f}")
                st.rerun()
            elif submitted_pag:
                st.error("Informe um valor de pagamento válido.")
                
    st.markdown("---")
    st.subheader("Histórico de Pagamentos e Correção de Lançamentos")
    if st.session_state.pagamentos.empty:
        st.info("Nenhum pagamento registrado ainda.")
    else:
        st.dataframe(st.session_state.pagamentos, use_container_width=True)
        
        st.markdown("### 🗑️ Excluir / Reverter Pagamento Incorreto")
        col_exc1, col_exc2 = st.columns([2, 1])
        pagamento_para_excluir = col_exc1.selectbox("Selecione o ID do Pagamento para Excluir", st.session_state.pagamentos["ID"].tolist())
        
        if col_exc2.button("Excluir Pagamento Selecionado", type="primary"):
            pag_info = st.session_state.pagamentos[st.session_state.pagamentos["ID"] == pagamento_para_excluir].iloc[0]
            id_contrato_afetado = int(pag_info["Contrato_ID"])
            valor_estornado = float(pag_info["Valor_Pago"])
            
            c_idx = st.session_state.contratos[st.session_state.contratos["ID"] == id_contrato_afetado].index
            if not c_idx.empty:
                idx_c = c_idx[0]
                saldo_atual_c = float(st.session_state.contratos.at[idx_c, "Saldo_Atual"])
                parcela_atual_c = int(st.session_state.contratos.at[idx_c, "Parcela_Atual"])
                
                novo_saldo_revertido = saldo_atual_c + valor_estornado
                
                st.session_state.contratos.at[idx_c, "Saldo_Atual"] = round(novo_saldo_revertido, 2)
                st.session_state.contratos.at[idx_c, "Parcela_Atual"] = max(0, parcela_atual_c - 1)
                st.session_state.contratos.at[idx_c, "Status"] = "Em dia"
            
            st.session_state.pagamentos = st.session_state.pagamentos[st.session_state.pagamentos["ID"] != pagamento_para_excluir]
            st.success(f"Pagamento ID {pagamento_para_excluir} excluído com sucesso! O saldo e as parcelas do contrato foram ajustados.")
            st.rerun()

# ==========================================
# 5. RELATÓRIO DE AUDITORIA
# ==========================================
elif menu == "Relatório de Auditoria":
    st.header("📋 Relatório de Auditoria para Conferência")
    st.markdown("Consolidado completo de todas as movimentações e contratos para prestação de contas e auditoria.")
    
    if st.session_state.contratos.empty and st.session_state.pagamentos.empty:
        st.info("Nenhum dado cadastrado ainda para gerar o relatório de auditoria.")
    else:
        st.subheader("1. Auditoria de Contratos")
        df_audit = st.session_state.contratos.copy()
        if not df_audit.empty and "Parcela_Atual" in df_audit.columns:
            df_audit["Parcelas"] = df_audit["Parcela_Atual"].astype(str) + " de " + df_audit["Total_Parcelas"].astype(str)
        st.dataframe(df_audit, use_container_width=True)
        
        st.subheader("2. Auditoria de Pagamentos Realizados")
        st.dataframe(st.session_state.pagamentos, use_container_width=True)
        
        csv_contratos = st.session_state.contratos.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Baixar Relatório de Contratos (CSV para Auditoria)",
            data=csv_contratos,
            file_name="auditoria_contratos.csv",
            mime="text/csv",
        )