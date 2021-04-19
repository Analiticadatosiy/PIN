import pandas as pd
import numpy as np
from pandas import DataFrame
from itertools import product
import streamlit as st
from PIL import Image
import base64

st.title("Optimización PIN - Incolmotos Yamaha")
img = Image.open("logo.png")
st.sidebar.image(img, width=250)

st.sidebar.subheader("Parámetros")
trm = st.sidebar.number_input('TRM', value=3650)
ciffob = st.sidebar.number_input('FOB/CIF', value=1.08)
integracion_mes=st.sidebar.number_input('Valor integración actual (simulador)')
fob = st.sidebar.number_input('FOB (USD)')
ckd_fijo = st.sidebar.number_input('CKD etapas anteriores (archivo modelo)')
local_entrada=st.sidebar.number_input('Valor integración etapas anteriores (archivo modelo)')
herramentales_fijos= st.sidebar.number_input('Inversión herramentales etapas anteriores (archivo modelo)')

# fob = 1341.87
# trm = 3650
# ciffob = 1.08
# integracion_mes = 265267.5813
# herramentales_fijos = 534950956
# ckd_fijo = 443483.772675727

data_file=st.file_uploader('Archivo',type=['xlsx'])
ejecucion=st.button('Ejecutar')

if data_file is not None and ejecucion is not None :

    #df_p2 = pd.read_excel("referenciasNMAX_modificado.xlsx", sheet_name='Hoja2')
    df_p2 = pd.read_excel(data_file, sheet_name='Unidades')
    Unidades_Producidas = np.array(df_p2.loc[:, 'Unidades_Producidas'])
    Fecha_unid=np.array(df_p2.loc[:, 'Mes'])
    Costo_CKD = fob * trm * ciffob
    Costo_CKD = Unidades_Producidas * Costo_CKD
    #df_p = pd.read_excel("referenciasNMAX_modificado.xlsx", sheet_name='Hoja1')
    
    #df_p3 = pd.read_excel("referenciasNMAX_modificado.xlsx", sheet_name='Hoja3')
    df_p3=pd.read_excel(data_file,sheet_name='Etapas_anteriores')
    Fecha_etapa_ant = np.array(df_p3.loc[:, 'Fecha_inicio'])
    Valor_unitario = np.array(df_p3.loc[:, 'Valor_unitario'])
    Fecha_comp_imp = np.array(df_p3.loc[:, 'Fecha_inicio_componentes'])
    Componentes_importados = np.array(df_p3.loc[:, 'Valor_componentes_importados'])

    
    sum_etapas_ant = []
    sum_comp_imp=[]
    for ff in Fecha_unid:
            acum = 0
            acum_comp=0
            contador = 0
            contador_comp=0
            for f in Fecha_etapa_ant:
                if ff >= f:
                    acum = Valor_unitario[contador] + acum
                contador = contador + 1

            for fc in Fecha_comp_imp:
                if ff >= fc:
                    acum_comp = Componentes_importados[contador_comp] + acum_comp
                contador_comp = contador_comp + 1

            sum_etapas_ant.append(acum)
            sum_comp_imp.append(acum_comp)
    costo_fijo = (Unidades_Producidas*sum_etapas_ant)+(Unidades_Producidas*sum_comp_imp)


    df_p=pd.read_excel(data_file,sheet_name='Candidatas')
    tamano = len(df_p.index)
    
    lista = list(product([0, 1], repeat=tamano))
    Precio_CKD = np.array(df_p.loc[:, 'Precio_CKD_CIF'])
    Precio_local = np.array(df_p.loc[:, 'Precio_local'])
    herramentales = np.array(df_p.loc[:, 'Herramentales'])
    Fecha_proy = np.array(df_p.loc[:, 'Fecha_inicio'])
    Referencia = np.array(df_p.loc[:, 'Referencia'])
    Nombre = np.array(df_p.loc[:, 'Nombre_pieza'])



    combinacion = []
    resultado = []
    cont=0
    vector_pin=[]

    for l in lista:
        sum_precio_local = []
        combinacion = np.array(l)
        comb_precio = combinacion * Precio_local
        comb_ckd = combinacion * Precio_CKD
        comb_herra = combinacion * herramentales
        sum_herramentales = sum(comb_herra)
        sum_ckd = sum(comb_ckd)
        sum_local = sum(comb_precio)
        for ff in Fecha_unid:
            acum = 0
            cont = 0
            for f in Fecha_proy:
                if ff >= f:
                    # print(str(f) + ' ' + str(ff))
                    acum = comb_precio[cont] + acum
                cont = cont + 1
            sum_precio_local.append(acum)
        local_mes = Unidades_Producidas * sum_precio_local
        CNM_mes = Unidades_Producidas * integracion_mes
        #resultado.append([combinacion, comb_precio, comb_herra, local_mes,
        #                  (Costo_CKD) - (local_mes),CNM_mes, sum_precio_local, sum_herramentales])

        CKD = pd.Series(Costo_CKD)
        CNM = pd.Series(CNM_mes)
        local = pd.Series(local_mes)
        CKD_Proy = pd.Series(Costo_CKD - local - costo_fijo)
        CNM_Proy = pd.Series(CNM + local + costo_fijo)
        # CKD_Proy=sum(CKD_Proy)
        df = pd.concat([CKD, CNM, CKD_Proy, CNM_Proy], axis=1)
        df = DataFrame(df.values, columns=['CKDo', 'CNM', 'CKDp', 'CNMp'])

        df_all = pd.DataFrame()
        df_p4=pd.read_excel(data_file,sheet_name='Totales_Anuales')
        df_all['Modelo']  = np.array(df_p4.loc[:, 'Modelo'])
        df_all['CKDp'] = np.array(df_p4.loc[:, 'CKDp'])
        df_all['CNMp'] = np.array(df_p4.loc[:, 'CNMp'])
        df_all = df_all.append({'Modelo': 'Modelo_Evaluado', 'CKDp': int(df['CKDp'].sum()), 'CNMp': int(df['CNMp'].sum())},
                               ignore_index=True)

        df_all['CKDp'] = df_all['CKDp'].astype(float)
        df_all['CNMp'] = df_all['CNMp'].astype(float)
        Importado = df_all['CKDp'].sum()
        Nal = df_all['CNMp'].sum()
        Total = Nal + Importado
        PIN = Nal / Total
        # print(Total)
        # print(Nal)

        Inversion = (sum_herramentales) + herramentales_fijos
        CKD_Tot = sum_ckd + ckd_fijo
        Local = sum_local + sum(Valor_unitario)
        Dif = CKD_Tot - Local
        Val = (sum_herramentales) / PIN / 100
        id=''.join(str(e) for e in combinacion)
        #vector_pin.append([str(id), PIN,(sum_herramentales),Val, Dif])
        vector_pin.append([str(id), PIN, ("{:.2%}".format(PIN)), sum_herramentales, ("${:,.0f}".format(sum_herramentales)),
            ("${:,.0f}".format(Val)), ("${:,.0f}".format(Dif))])
        #print(vector_pin)"${:,.2f}
        


    df_final = pd.DataFrame(vector_pin,columns=['Mezcla', 'PIN_sin_formato','PIN','Herramentales_sinFormato', 'Herramentales','$Por%','DifCKD'])
    df_final['Mezcla']=df_final['Mezcla'].apply(str)
    #df_final=df_final[df_final['PIN']>0.1777]
    #df_final=df_final.sort_values(by='$Por%', ascending='True')
    df_final = df_final.sort_values(by=['Herramentales_sinFormato', 'PIN_sin_formato'], ascending=[True, False])
    df_final.drop(['Herramentales_sinFormato', 'PIN_sin_formato'], axis=1, inplace=True)
    #print(df_final)
    #df_final.to_csv('resultados.csv', sep=";", decimal=',', index=False)
    #df_final.to_excel('resultados.xlsx', index=False)
    soluciones=df_final.head(15).index
   

    lista_soluciones = st.number_input('Cuántas soluciones desea ver:')

    for j in range(0, int(lista_soluciones)):
        st.markdown("### Solución %s " % (j+1))
        #md_results = f"Solución **{j:.0f}**"
        #st.markdown(md_results)
        text = f"Piezas **a integrar** en esta solución: "
        st.markdown(text)
        temp = lista[soluciones[j]]
        count=0
        index_solution=[]
        for i in temp:
            if i==1:
               index_solution.append(count)
            count=count+1
        #st.write(index_solution)
        #st.write(df_p.iloc[index_solution])
        #st.table(df_p.iloc[index_solution])
        st.table(df_p.iloc[index_solution].assign(hack='').set_index('hack'))
        #st.dataframe(df_p.iloc[index_solution].assign(hack='').set_index('hack'))
        st.write(df_final.loc[soluciones[j]])
        
    st.markdown("La ejecución **finalizó**")

    def get_table_download_link(df):
      """Generates a link allowing the data in a given panda dataframe to be downloaded
      in:  dataframe
      out: href string
      """
      csv = df.to_csv(index=False)
      b64 = base64.b64encode(csv.encode()).decode()  # some strings <-> bytes conversions necessary here
      href = f'<a href="data:file/csv;base64,{b64}">Download csv file</a>'
    
    #Descargar los resultados
    csv = df_final.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()  # some strings <-> bytes conversions necessary here
    href = f'<a href="data:file/csv;base64,{b64}">Download CSV File</a> (right-click and save as &lt;some_name&gt;.csv)'
    st.markdown(href, unsafe_allow_html=True)

    




