import streamlit as st
import datetime
import gspread
from google.oauth2.service_account import Credentials
import matplotlib.pyplot as plt
import numpy as np
import json

# --- CONFIGURAZIONE PAGINA E BRAND ---
st.set_page_config(page_title="GÉNERA | ISA-Q", layout="centered")

# Palette Colori GÉNERA
COLORS = {
    'primary': '#1A3A5F',    # Blu Notte
    'secondary': '#5D8A78',  # Verde Salvia
    'accent': '#D9A552',     # Ocra
    'bg': '#F4F4F4'
}

# --- FUNZIONE SALVATAGGIO GOOGLE SHEETS ---
def save_to_google_sheets(data_row):
    try:
        # Recupera il blocco JSON dai secrets
        json_text = st.secrets["gcp_json_text"]
        creds_dict = json.loads(json_text)
        
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        gc = gspread.authorize(credentials)
        
        sh = gc.open_by_url(st.secrets["private_sheet_url"])
        sh.sheet1.append_row(data_row)
        return True
    except Exception as e:
        st.error(f"Errore tecnico nel salvataggio: {e}")
        return False

# --- FUNZIONE GRAFICO RADAR ---
def create_radar_chart(scores):
    categories = list(scores.keys())
    values = list(scores.values())
    values += values[:1] # Chiude il cerchio
    
    angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
    angles += angles[:1]
    
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    
    # Stile Assi
    plt.xticks(angles[:-1], categories, color=COLORS['primary'], size=9, weight='bold')
    ax.set_rlabel_position(0)
    plt.yticks([6, 12, 18], ["6", "12", "18"], color="grey", size=7)
    plt.ylim(0, 20)
    
    # Plot
    ax.plot(angles, values, color=COLORS['primary'], linewidth=2, linestyle='solid')
    ax.fill(angles, values, color=COLORS['secondary'], alpha=0.4)
    ax.spines['polar'].set_visible(False)
    
    return fig

# --- APP PRINCIPALE ---
def main():
    # Intestazione Brand
    st.markdown(f"<h1 style='color:{COLORS['primary']}; text-align: center;'>GÉNERA</h1>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='color:{COLORS['secondary']}; text-align: center;'>Impact Self-Assessment (ISA-Q)</h3>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Introduzione (Testo fornito)
    st.info("**Benvenuto/a.** L'ISA-Q è lo \"Strumento Zero\" di GÉNERA. È il punto di ingresso per qualsiasi percorso (individuale o aziendale).")
    
    with st.expander("ℹ️ Leggi la struttura dello strumento"):
        st.markdown("""
        **Obiettivo:** Fornire una valutazione preliminare dell’"indice di impatto personale" (Persona Impact Index), attraverso la misurazione della percezione soggettiva delle 5 dimensioni concettuali del nostro modello.
        
        **Formato:** Questionario digitale.
        
        **Scala di risposta:** Likert a 6 punti (1 = ritengo l’affermazione totalmente falsa; 6 = ritengo l’affermazione totalmente vero), per forzare una presa di posizione.
        """)

    # --- SEZIONE 1: ANAGRAFICA ---
    st.subheader("1. Anagrafica")
    st.write("I dati raccolti mantengono l'anonimato ma sono d'aiuto nell'interpretazione dei risultati.")
    
    col1, col2 = st.columns(2)
    with col1:
        genere = st.selectbox("Genere", 
            ["Seleziona...", "Maschile", "Femminile", "Non binario", "Preferisco non dichiararlo"])
        eta = st.selectbox("Età", 
            ["Seleziona...", "Fino a 20 anni", "21-30 anni", "31-40 anni", "41-50 anni", "51-60 anni", "61-70 anni", "Più di 70 anni"])
    
    with col2:
        scolarita = st.selectbox("Scolarità", 
            ["Seleziona...", "Licenza media inferiore", "Qualifica professionale", "Diploma scuola media superiore", 
             "Laurea triennale", "Laurea magistrale o specialistica", "Certificazione post laurea"])

    anagrafica_ok = (genere != "Seleziona...") and (eta != "Seleziona...") and (scolarita != "Seleziona...")
    st.markdown("---")

    # --- SEZIONE 2: ITEM (QUESTIONARIO) ---
    st.subheader("2. Autovalutazione")
    st.write("Valuta le affermazioni da **1 (Totalmente Falso)** a **6 (Totalmente Vero)**.")

    # Struttura dati: (Domanda, è_Inverso, Dimensione)
    questions = [
        # Dimensione 1: Autonomia e Competenza
        ("Sento che le mie attività quotidiane riflettono i miei valori e le mie convinzioni personali.", False, "Autonomia e Competenza"),
        ("Quando affronto un compito difficile, ho fiducia nella mia capacità di padroneggiarlo con le risorse a mia disposizione.", False, "Autonomia e Competenza"),
        ("Mi capita spesso di svolgere il mio lavoro solo perché mi è stato imposto, senza sentirlo veramente 'mio'.", True, "Autonomia e Competenza"),
        
        # Dimensione 2: Potere Personale
        ("Di fronte a un problema lavorativo, mi attivo immediatamente per modificare gli elementi che sono sotto il mio controllo.", False, "Potere Personale"),
        ("Sento di avere l'autorità e la capacità necessarie per influenzare i processi decisionali che riguardano il mio ruolo.", False, "Potere Personale"),
        ("Ho la sensazione che la mia crescita professionale dipenda più dal caso o dalle decisioni altrui che dal mio impegno.", True, "Potere Personale"),
        
        # Dimensione 3: Coerenza e Significato
        ("Comprendo chiaramente come il mio lavoro si inserisce nel quadro generale e negli obiettivi dell'organizzazione.", False, "Coerenza e Significato"),
        ("Considero le sfide lavorative come occasioni che valgono l'investimento di tempo ed energia.", False, "Coerenza e Significato"),
        ("Molto spesso mi sembra che le richieste che ricevo siano confuse, imprevedibili o prive di una logica chiara.", True, "Coerenza e Significato"),
        
        # Dimensione 4: Impatto e Futuro
        ("Mi impegno attivamente per trasmettere le mie conoscenze e competenze ai colleghi o ai collaboratori più giovani.", False, "Impatto e Futuro"),
        ("Mi dà soddisfazione sapere che i risultati del mio lavoro avranno un impatto positivo sugli altri anche in futuro.", False, "Impatto e Futuro"),
        ("Tendo a focalizzarmi esclusivamente sui miei task individuali, senza preoccuparmi della crescita del team o del contesto.", True, "Impatto e Futuro"),
        
        # Dimensione 5: Flessibilità Evolutiva
        ("Quando vivo un fallimento professionale, riesco a recuperare velocemente l'equilibrio e a ripartire.", False, "Flessibilità Evolutiva"),
        ("Considero i cambiamenti organizzativi inattesi come opportunità per sviluppare nuove competenze.", False, "Flessibilità Evolutiva"),
        ("In periodi di forte stress, faccio fatica a trovare soluzioni creative e tendo a irrigidirmi sulle vecchie abitudini.", True, "Flessibilità Evolutiva"),
    ]

    responses = {}
    with st.form("isa_form"):
        for i, (q_text, is_reverse, dim) in enumerate(questions):
            st.markdown(f"**{i+1}.** {q_text}")
            responses[i] = st.slider(f"Risposta {i+1}", 1, 6, 3, key=i, label_visibility="collapsed")
            st.write("") 
        
        submitted = st.form_submit_button("Calcola Profilo")

    # --- SEZIONE 3: OUTPUT E FEEDBACK ---
    if submitted:
        if not anagrafica_ok:
            st.error("Per favore, compila tutti i campi dell'anagrafica prima di procedere.")
        else:
            # Calcolo Punteggi
            scores = {
                "Autonomia e Competenza": 0,
                "Potere Personale": 0,
                "Coerenza e Significato": 0,
                "Impatto e Futuro": 0,
                "Flessibilità Evolutiva": 0
            }
            
            for i, (q_text, is_reverse, dim) in enumerate(questions):
                val = responses[i]
                if is_reverse:
                    val = 7 - val # Inversione scala 1-6
                scores[dim] += val

            total_score = sum(scores.values())

            # Logica di Feedback (Nuovi Profili)
            feedback_title = ""
            feedback_text = ""
            color_class = ""

            if 15 <= total_score <= 30:
                feedback_title = "IMPATTO LATENTE (Fase passiva profonda)"
                color_class = "warning"
                feedback_text = (
                    "In base ai risultati del test sembri al momento vivere una fase di adattamento profondamente “passivo”. "
                    "Non sembri avere consapevolezza delle tue potenzialità e non sai, di conseguenza, di quali risorse puoi disporre "
                    "e quali ti potrebbero servire per attuarle.\n\n"
                    "**Azione suggerita:** focalizzati sullo sviluppare consapevolezza attraverso strumenti di autovalutazione "
                    "che ti consentano anche di valutare i tuoi punti di forza e le aree di sviluppo."
                )
            elif 31 <= total_score <= 45:
                feedback_title = "IMPATTO LATENTE (Fase tendenzialmente passiva)"
                color_class = "warning"
                feedback_text = (
                    "In base ai risultati del test sembri al momento vivere una fase di adattamento tendenzialmente “passivo”. "
                    "Non sembri avere grande consapevolezza delle tue potenzialità e non sai, di conseguenza, di quali risorse puoi disporre "
                    "e quali ti potrebbero servire per attuarle.\n\n"
                    "**Azione suggerita:** focalizzati sullo sviluppare maggiore consapevolezza attraverso strumenti di autovalutazione "
                    "che ti consentano anche di valutare i tuoi punti di forza e le aree di sviluppo."
                )
            elif 46 <= total_score <= 58:
                feedback_title = "IMPATTO EMERGENTE (Discontinuità attuativa)"
                color_class = "info"
                feedback_text = (
                    "In base ai risultati del test sembri essere fuori da una fase passiva di adattamento dato che mostri una certa "
                    "consapevolezza delle tue potenzialità, tuttavia presenti frequentemente anche una importante discontinuità nell’attuarle.\n\n"
                    "**Azione suggerita:** focalizzati sullo sviluppo delle soft skill – in particolare quelle relative alla learning agility – "
                    "che potrebbero consentirti di trasformare le tue potenzialità in possibilità praticabili mediante il ricorso a strumenti facilitanti l’autoapprendimento."
                )
            elif 59 <= total_score <= 70:
                feedback_title = "IMPATTO EMERGENTE (Consapevolezza in crescita)"
                color_class = "info"
                feedback_text = (
                    "In base ai risultati del test mostri consapevolezza circa le tue potenzialità, pur evidenziando una certa discontinuità nell’attuarle.\n\n"
                    "**Azione suggerita:** focalizzati sullo sviluppo delle soft skill – in particolare quelle relative alla gestione dell’energia – "
                    "che potrebbero consentirti di trasformare le tue potenzialità in possibilità praticabili mediante il ricorso a strumenti facilitanti l’autoapprendimento."
                )
            elif 71 <= total_score <= 80:
                feedback_title = "IMPATTO GENERATIVO (Performante)"
                color_class = "success"
                feedback_text = (
                    "Dimostri di avere un motore di competenza e benessere performante: sei consapevole delle tue potenzialità e conosci le tue risorse personali.\n\n"
                    "**Azione suggerita:** metterle a disposizione anche degli altri, sviluppando una visione sistemica ed una leadership empowering."
                )
            elif 81 <= total_score <= 90:
                feedback_title = "IMPATTO GENERATIVO (Molto performante)"
                color_class = "success"
                feedback_text = (
                    "Dimostri di avere un motore di competenza e benessere molto performante: sei decisamente consapevole delle tue potenzialità e delle tue risorse personali.\n\n"
                    "**Azione suggerita:** metterle a disposizione anche degli altri, sviluppando una visione sistemica ed una leadership empowering."
                )

            # --- VISUALIZZAZIONE ---
            st.markdown("---")
            st.subheader("Il tuo Profilo di Impatto")
            
            col_chart, col_text = st.columns([1, 1])
            
            with col_chart:
                fig = create_radar_chart(scores)
                st.pyplot(fig)
            
            with col_text:
                st.metric("Punteggio Totale", f"{total_score}/90")
                
                # Visualizzazione Box Colorato
                if color_class == "warning":
                    st.warning(f"### {feedback_title}\n\n{feedback_text}")
                elif color_class == "info":
                    st.info(f"### {feedback_title}\n\n{feedback_text}")
                else:
                    st.success(f"### {feedback_title}\n\n{feedback_text}")

                with st.expander("Dettaglio Punteggi per Dimensione"):
                    for dim, val in scores.items():
                        st.write(f"**{dim}:** {val}/18")

            # --- SALVATAGGIO CLOUD ---
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Riga ordinata secondo il nuovo standard
            row_data = [
                timestamp, genere, eta, scolarita, total_score,
                scores["Autonomia e Competenza"], 
                scores["Potere Personale"], 
                scores["Coerenza e Significato"], 
                scores["Impatto e Futuro"], 
                scores["Flessibilità Evolutiva"]
            ]
            
            with st.spinner("Salvataggio risultati in corso..."):
                if save_to_google_sheets(row_data):
                    st.success("✅ Risultati salvati correttamente nel database.")
                else:
                    st.error("⚠️ Test completato, ma errore nel salvataggio remoto.")

if __name__ == "__main__":
    main()
