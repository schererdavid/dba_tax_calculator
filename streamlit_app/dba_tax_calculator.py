import streamlit as st
import pandas as pd
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))  # robust, funktioniert überall


rates = pd.read_excel(os.path.join(BASE_DIR, "estv_income_rates.xlsx"), header=3)
sc_f = pd.read_excel(os.path.join(BASE_DIR, "estv_scales_fed.xlsx"), header=5)
sc_c = pd.read_excel(os.path.join(BASE_DIR, "estv_scales_zh.xlsx"), header=5)


st.write("# Income tax estimation Switzerland-Liechtenstein DBA")
st.write("Attention:")
st.markdown("- Absolut no guranatee for correctness of any result!")
st.markdown("- Supports only the tax year 2025 at the moment")
st.markdown("- Does not support wealth or any additional tax at the moment")
st.markdown("- LI Town Tax at 150%")

st.write("## Switzerland")
tax_in_c = int(st.text_input("Cantonal taxable income:", value="100000"))
tax_in_f = int(st.text_input("Federal taxable income:", value="100000"))
gemeinde = st.selectbox("City", rates['Gemeinde'])


subject = st.selectbox("Steuersubjekt", sc_c['Steuersubjekt'].unique())




rates_filtered = rates[rates['Gemeinde'] == gemeinde]
rate_c = rates_filtered['Kanton.1'].values[0]/100
rate_g = rates_filtered['Gemeinde.1'].values[0]/100

temp = tax_in_c
cumulated_c_tax = 0
amount_cum = 0
for i, row in sc_c[sc_c['Steuersubjekt'] == subject].iterrows():
    amount = row['Für die nächsten CHF']
    rate = row['Zusätzlich %']/100
    if temp < amount:
        # we reached the end
        cumulated_c_tax += rate * temp
        #print("rate * temp:", rate, "*", temp)
        break
    else:
        cumulated_c_tax += rate * amount
        #print("rate * temp:", rate, "*", amount)
        
    temp -= amount
        




temp = tax_in_f
cumulated_f_tax = 0
amount_cum = 0
for i, row in sc_f[sc_f['Steuersubjekt'] == subject].iterrows():
    amount = row['Steuerbares Einkommen CHF']
    rate = row['Zusätzlich %']/100
    if temp < amount:
        # we reached the end
        cumulated_f_tax += rate * temp
        #print("rate * temp:", rate, "*", temp)
        break
    else:
        cumulated_f_tax += rate * amount
        #print("rate * temp:", rate, "*", amount)
        
    temp -= amount
    
st.write("Taxes when working 100% in Switzerland:")
g_tax = (cumulated_c_tax) * rate_g

st.markdown(f"- City: CHF {g_tax:.2f}")
c_tax = cumulated_c_tax * rate_c
st.markdown(f"- Canton: CHF {c_tax:.2f}")    
        
st.markdown(f"- Federal: CHF {cumulated_f_tax:.2f}")
f_tax = cumulated_f_tax

total_ch = c_tax + g_tax + f_tax
st.markdown(f"- Total: CHF {total_ch:.2f}")


sc_li = pd.read_excel(os.path.join(BASE_DIR, "tax_li.xlsx"), sheet_name="Sheet2")


st.write("## Liechtenstein ")
tax_in_li = int(st.text_input("Taxable income", value="100000"))

row = sc_li[((sc_li['from'] <= tax_in_li) & (tax_in_li <= sc_li['to'])) | (( sc_li['from'] <= tax_in_li) & sc_li['to'].isna())]
rate = row['rate'].values[0]
minus = row['minus'].values[0]
tax_li_land = rate * tax_in_li - minus
tax_li_gemeinde = tax_li_land * 1.5
total_li = tax_li_land + tax_li_gemeinde

st.write("Taxes when working 100% in Liechtenstein:")
st.markdown(f"- Landessteuer: CHF {tax_li_land:.2f}")
st.markdown(f"- Additional Gemeindesteuer (based on 150%): CHF {tax_li_gemeinde:.2f}")
st.markdown(f"- Total: CHF {total_li:.2f}")

st.write("## End calculation ")

nichtrueckkehrtage = st.number_input("Number of Nichtrückkehrtage", value=48)

if nichtrueckkehrtage >= 45:

    arbeitstage_li = st.number_input("Number of working days in Liechtenstein", value=140)
    arbeitstage_ch = st.number_input("Number of working days in Switzerland", value=85)
    arbeitstage_other = st.number_input("Number of working days elsewhere", value=0)

    total_working_days = arbeitstage_li + arbeitstage_ch + arbeitstage_other
    
    # method CH
    tax_ch_method_ch = (total_working_days - arbeitstage_li) / total_working_days

    # method LI
    #tax_li_method_li =  nichtrueckkehrtage / 240
    tax_li_method_li = (240 - (arbeitstage_other+arbeitstage_ch)) / 240
    tax_li_method_ch = arbeitstage_li / total_working_days
    
    st.write(f"### Tax splitting according to Switzerland:")
    st.write(f"Switzerland: {tax_ch_method_ch:.2f}%")
    total_taxes_to_pay_to_CH = tax_ch_method_ch * total_ch
    st.write(f"Total taxes to pay to CH: CHF {total_taxes_to_pay_to_CH:.2f}")
    gemeinde_taxes_to_pay_to_CH = tax_ch_method_ch * g_tax
    cantonal_taxes_to_pay_to_CH = tax_ch_method_ch * c_tax
    federal_taxes_to_pay_to_CH = tax_ch_method_ch * f_tax
    st.write(f"Gemeinde taxes to pay to CH: CHF {gemeinde_taxes_to_pay_to_CH:.2f}")
    st.write(f"Cantonal taxes to pay to CH: CHF {cantonal_taxes_to_pay_to_CH:.2f}")
    st.write(f"Federal taxes to pay to CH: CHF {federal_taxes_to_pay_to_CH:.2f}")


    st.write(f"### Tax splitting according to Liechtenstein:")
    st.write(f"Default method Liechtenstein: {tax_li_method_li:.2f}%")
    st.write(f"Exact method: {tax_li_method_ch:.2f}%")
    method = st.radio(
        "Choose method for Liechtenstein (lower recommended):",
        ["Default method", "Exact method"],
        captions=[
            "Default method",
            "Exact method"
        ],
    )

    if method == 'Exact method':
        tax_li = tax_li_method_ch
    else: 
        tax_li = tax_li_method_li

    total_taxes_to_pay_to_LI = tax_li * total_li
    land_taxes_to_pay_to_LI = tax_li * tax_li_land
    gemeinde_total_taxes_to_pay_to_LI = tax_li * tax_li_gemeinde
    st.write(f"Total taxes to pay to LI: CHF {total_taxes_to_pay_to_LI:.2f}")
    st.write(f"Gemeinde taxes to pay to LI: CHF {gemeinde_total_taxes_to_pay_to_LI:.2f}")
    st.write(f"Land taxes to pay to LI: CHF {land_taxes_to_pay_to_LI:.2f}")
    
    st.write(f"### Total and additional information")
    total_taxes = total_taxes_to_pay_to_LI + total_taxes_to_pay_to_CH
    st.write(f"Total taxes: CHF {total_taxes:.2f}")
    st.write(f"Total taxes (monthly): CHF {total_taxes/12:.2f}")

    if tax_li + tax_ch_method_ch > 1:
        st.write(f"Since {100*tax_li:.2f}% + {100*tax_ch_method_ch:.2}% > 100% you will be doppelbesteuert.")
    elif tax_li + tax_ch_method_ch == 1:
        st.write(f"Since {100*tax_li:.2f}% + {100*tax_ch_method_ch:.2}% = 100% both calculation methods end up with the same result.")
    else:
        st.write(f"Since {100*tax_li:.2f}% + {100*tax_ch_method_ch:.2}% < 100% some of your income will not be taxed at all.")

    personal_tax_rate = (total_taxes / ((tax_in_li + ((tax_in_c + tax_in_f) / 2)) / 2)) * 100
    st.write(f"Personal tax rate based on average taxable income (CH/LI): {personal_tax_rate:.2f}%",)

    savings = (total_ch - total_li) / (((52-5)*5)-15)
    st.write(f"Savings per day working in Liechtenstein (5 weeks vacation, 15 days holidays):  CHF {savings:.2f}")
    
else:
    st.write("Nichtrückkehrtage < 45, you are a Grenzgänger and all taxes are paid in Switzerland:")
    st.markdown(f"- City: CHF {g_tax:.2f}")
    st.markdown(f"- Canton: CHF {c_tax:.2f}")         
    st.markdown(f"- Federal: CHF {cumulated_f_tax:.2f}")
    st.markdown(f"- Total: CHF {total_ch:.2f}")