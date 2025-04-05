"""
Press Release Distribution Agent - Frontend

This module provides a Streamlit-based frontend for the press release distribution agent.
It includes a human-in-the-loop approval process for each step of the workflow.

Key features:
- User-friendly interface for press release generation
- Topic extraction and editing
- Recipient review and approval
- Email content preview and approval
- Social media posting status display
"""

import streamlit as st
from agent import get_workflow, AgentState
from utils import extract_topics
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('press_release_agent.frontend')

# Get the compiled workflow from the agent module
app = get_workflow()

def main():
    """Main function to run the Streamlit app."""
    # Initialize session state for Streamlit
    if "state" not in st.session_state:
        st.session_state.state = {
            "topic": "",
            "press_release": "",
            "press_release_url": "",
            "recipients": [],
            "email_status": {},
            "email_url": "",
            "social_media_status": {},
            "current_step": "initial",
            "approved": False,
            "topics": []  # Add topics to state
        }

    st.title("Agente di Distribuzione Comunicati Stampa")

    # Topic input section
    topic = st.text_input("Inserisci l'argomento del tuo comunicato stampa:", value=st.session_state.state["topic"])
    if topic and topic != st.session_state.state["topic"]:
        st.session_state.state["topic"] = topic
        # Generate press release immediately when topic is entered
        st.session_state.state = app.invoke(st.session_state.state)

    # State-specific UI components
    if st.session_state.state["current_step"] == "press_release":
        st.subheader("Fase 1: Rivedi il Comunicato Stampa Generato")
        st.info("Per favore rivedi attentamente il comunicato stampa generato. Nessun contenuto verrà memorizzato o inviato fino alla tua approvazione.")
        
        press_release = st.text_area("Comunicato Stampa:", value=st.session_state.state["press_release"], height=300)
        
        # Confirmation buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Approva e Procedi ai Topic"):
                st.session_state.state["press_release"] = press_release
                st.session_state.state["approved"] = True
                # Extract topics and move to topics step
                topics = extract_topics(press_release)
                st.session_state.state["topics"] = [t.strip() for t in topics.split(',')]
                st.session_state.state["current_step"] = "topics"
                st.experimental_rerun()
        with col2:
            if st.button("Rigenera Comunicato"):
                st.session_state.state = app.invoke(st.session_state.state)
                st.experimental_rerun()

    elif st.session_state.state["current_step"] == "topics":
        st.subheader("Fase 2: Rivedi e Modifica i Topic")
        st.info("Rivedi i topic estratti dal comunicato stampa. Puoi modificarli, aggiungerne di nuovi o rimuoverli prima di procedere.")
        
        # Show and allow editing of topics
        edited_topics = []
        for i, topic in enumerate(st.session_state.state["topics"]):
            col1, col2 = st.columns([3, 1])
            with col1:
                edited_topic = st.text_input(f"Topic {i+1}:", value=topic)
                edited_topics.append(edited_topic)
            with col2:
                if st.button("Rimuovi", key=f"remove_{i}"):
                    edited_topics.pop(i)
                    st.session_state.state["topics"] = edited_topics
                    st.experimental_rerun()
        
        # Allow adding new topics
        new_topic = st.text_input("Aggiungi nuovo topic:")
        if st.button("Aggiungi") and new_topic:
            edited_topics.append(new_topic)
            st.session_state.state["topics"] = edited_topics
            st.experimental_rerun()
        
        # Store final topics in state
        st.session_state.state["topics"] = edited_topics
        
        # Confirmation buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Approva e Cerca Destinatari"):
                st.session_state.state["approved"] = True
                st.session_state.state = app.invoke(st.session_state.state)
        with col2:
            if st.button("Torna al Comunicato"):
                st.session_state.state["current_step"] = "press_release"
                st.session_state.state["approved"] = False
                st.experimental_rerun()

    elif st.session_state.state["current_step"] == "recipients":
        st.subheader("Fase 3: Rivedi Destinatari e Contenuto Email")
        st.info("Per favore rivedi attentamente i destinatari e il contenuto dell'email. Nessuna email verrà inviata fino alla tua approvazione.")
        
        # Show recipients
        st.write("Destinatari:")
        for recipient in st.session_state.state["recipients"]:
            st.write(f"- {recipient['name']} ({recipient['email']}) - {recipient.get('role', 'Ruolo non specificato')}")
        
        # Show email preview
        st.write("Contenuto Email:")
        email_content = f"""Oggetto: Comunicato Stampa: {st.session_state.state["topic"]}

Gentile Redattore,

La contatto per condividere un comunicato stampa che potrebbe interessare i suoi lettori.

{st.session_state.state["press_release"]}

Cordiali saluti,
[Il Suo Nome]"""
        
        st.text_area("Email:", value=email_content, height=300, disabled=True)
        
        # Confirmation buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Approva e Invia Email"):
                st.session_state.state["approved"] = True
                st.session_state.state = app.invoke(st.session_state.state)
        with col2:
            if st.button("Torna ai Topic"):
                st.session_state.state["current_step"] = "topics"
                st.session_state.state["approved"] = False
                st.experimental_rerun()

    elif st.session_state.state["current_step"] == "email":
        st.subheader("Fase 4: Stato Distribuzione Email")
        st.write(st.session_state.state["email_status"])
        if st.button("Procedi ai Social Media"):
            st.session_state.state["approved"] = True
            st.session_state.state = app.invoke(st.session_state.state)

    elif st.session_state.state["current_step"] == "social_media":
        st.subheader("Fase 5: Stato Pubblicazione Social Media")
        st.write(st.session_state.state["social_media_status"])
        if st.button("Completa Processo"):
            st.session_state.state = {
                "topic": "",
                "press_release": "",
                "press_release_url": "",
                "recipients": [],
                "email_status": {},
                "email_url": "",
                "social_media_status": {},
                "current_step": "initial",
                "approved": False,
                "topics": []
            }

if __name__ == "__main__":
    main()