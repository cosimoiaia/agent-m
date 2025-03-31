"""
Press Release Distribution Agent

This module implements a LangGraph-based workflow for generating and distributing press releases.
The agent uses Groq for text generation, AWS S3 for cloud storage, and various APIs for distribution.
The interface is built with Streamlit and includes human-in-the-loop approval steps.

Key features:
- Press release generation using Groq
- Web search for relevant recipients
- Email distribution
- Social media posting
- Cloud storage of all generated content
- Human-in-the-loop approval process
"""

import os
import streamlit as st
from langgraph.graph import Graph, StateGraph
from typing import Dict, TypedDict, Annotated, Sequence, Any, List
from groq import Groq
from dotenv import load_dotenv
import json
import time
from utils import (
    search_recipients,
    send_email,
    post_to_social_media,
    extract_topics
)
from cloud_storage import CloudStorage
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('press_release_agent')

# Load environment variables from .env file
load_dotenv()

# Initialize Groq client for text generation
logger.info("Initializing Groq client")
try:
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    logger.info("Successfully initialized Groq client")
except Exception as e:
    logger.error(f"Failed to initialize Groq client: {str(e)}")
    raise

# Get Groq configuration from environment variables with defaults
GROQ_MODEL = os.getenv("GROQ_MODEL", "mixtral-8x7b-32768")
GROQ_TEMPERATURE = float(os.getenv("GROQ_TEMPERATURE", "0.7"))

# Initialize cloud storage for persistent data
logger.info("Initializing cloud storage")
try:
    cloud_storage = CloudStorage()
    logger.info("Successfully initialized cloud storage")
except Exception as e:
    logger.error(f"Failed to initialize cloud storage: {str(e)}")
    raise

class AgentState(TypedDict):
    """
    Typed dictionary defining the state of the press release distribution agent.
    
    Attributes:
        topic (str): The main topic of the press release
        press_release (str): The generated press release content
        press_release_url (str): S3 URL where the press release is stored
        recipients (list): List of recipient dictionaries with contact information
        email_status (dict): Status of email distribution attempts
        email_url (str): S3 URL where email details are stored
        social_media_status (dict): Status of social media posting attempts
        current_step (str): Current step in the workflow
        approved (bool): Whether the current step has been approved by the user
        topics (list): List of topics extracted from the press release
    """
    topic: str
    press_release: str
    press_release_url: str
    recipients: list
    email_status: dict
    email_url: str
    social_media_status: dict
    current_step: str
    approved: bool
    topics: list

def press_release_writer(state: AgentState) -> AgentState:
    """
    Generate a press release using Groq based on the given topic.
    
    Args:
        state (AgentState): Current state of the agent
        
    Returns:
        AgentState: Updated state with generated press release
        
    Raises:
        Exception: If there is an error generating the press release
    """
    logger.info(f"Generating press release for topic: {state['topic']}")
    
    try:
        prompt = f"""Scrivi un comunicato stampa professionale in italiano su {state['topic']}. 
        Includi un titolo accattivante, un sottotitolo e un corpo del testo con citazioni e dettagli rilevanti.
        Formattalo in un formato standard di comunicato stampa.
        Assicurati che il tono sia professionale e adatto al mercato italiano."""
        
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=GROQ_TEMPERATURE,
        )
        
        state["press_release"] = response.choices[0].message.content
        state["current_step"] = "press_release"  # Changed back to press_release step
        state["approved"] = False  # Require approval
        
        # Store press release in cloud storage
        content = json.dumps({
            "topic": state["topic"],
            "content": state["press_release"],
            "timestamp": datetime.now().isoformat()
        }).encode('utf-8')
        
        state["press_release_url"] = cloud_storage.store_press_release(state["topic"], content)
        logger.info("Successfully stored press release in cloud storage")
        
        return state
    except Exception as e:
        logger.error(f"Error generating press release: {str(e)}")
        raise

def recipient_search(state: AgentState) -> AgentState:
    """Search for relevant media contacts in the Italian market using web search."""
    logger.info("Searching for potential recipients")
    
    try:
        # Use the confirmed topics for search
        recipients = search_recipients(state["topics"], country="it")
        
        if not recipients:
            st.error("Nessun destinatario trovato. Prova con un argomento diverso o verifica la tua News API key.")
            return state
            
        state["recipients"] = recipients
        state["current_step"] = "recipients"
        state["approved"] = False  # Require approval
        
        logger.info(f"Found {len(state['recipients'])} potential recipients")
        
    except Exception as e:
        logger.error(f"Errore nella ricerca dei destinatari: {str(e)}")
        state["recipients"] = []
    
    return state

def email_distributor(state: AgentState) -> AgentState:
    """
    Store press release in cloud storage, send emails, and store email details.
    Only performs actions after explicit user approval.
    
    Args:
        state (AgentState): Current state of the agent
        
    Returns:
        AgentState: Updated state with email distribution status and storage URLs
        
    Raises:
        Exception: If there is an error during email distribution or storage
    """
    logger.info("Starting email distribution")
    
    try:
        if not state.get("press_release"):
            raise Exception("Press release content is missing")
            
        if not state.get("recipients"):
            raise Exception("No recipients found")
            
        # Only proceed with storage and sending if explicitly approved
        if state.get("approved", False):
            # Try to store press release in cloud storage
            try:
                press_release_data = {
                    "topic": state["topic"],
                    "content": state["press_release"]
                }
                state["press_release_url"] = cloud_storage.store_press_release(
                    state["topic"],
                    json.dumps(press_release_data).encode('utf-8')
                )
            except Exception as e:
                print(f"Warning: Failed to store press release in cloud storage: {str(e)}")
                state["press_release_url"] = ""
                
            # Send emails and get status
            email_status = send_email(state["recipients"], state["press_release"])
            state["email_status"] = email_status
            
            # Try to store email details in cloud storage
            try:
                email_details = {
                    "topic": state["topic"],
                    "press_release": state["press_release"],
                    "recipients": state["recipients"],
                    "email_status": email_status
                }
                state["email_url"] = cloud_storage.store_email(
                    state["topic"],
                    json.dumps(email_details).encode('utf-8')
                )
            except Exception as e:
                print(f"Warning: Failed to store email details in cloud storage: {str(e)}")
                state["email_url"] = ""
        
        state["current_step"] = "email"
        state["approved"] = False  # Reset approval for next step
        return state
    except Exception as e:
        logger.error(f"Error during email distribution: {str(e)}")
        raise

def social_media_poster(state: AgentState) -> AgentState:
    """
    Post the press release to various social media platforms.
    Only performs actions after explicit user approval.
    
    Args:
        state (AgentState): Current state of the agent
        
    Returns:
        AgentState: Updated state with social media posting status
        
    Raises:
        Exception: If there is an error posting to social media
    """
    logger.info("Starting social media posting")
    
    try:
        if not state.get("press_release"):
            raise Exception("Press release content is missing")
            
        # Only proceed with posting if explicitly approved
        if state.get("approved", False):
            # Post to social media and get status
            social_media_status = post_to_social_media(state["press_release"])
            if not social_media_status:
                raise Exception("Failed to post to social media")
                
            state["social_media_status"] = social_media_status
        
        state["current_step"] = "social_media"
        state["approved"] = False  # Reset approval for next step
        return state
    except Exception as e:
        logger.error(f"Error posting to social media: {str(e)}")
        raise

# Create and configure the LangGraph workflow
workflow = StateGraph(AgentState)

# Add nodes to the workflow
workflow.add_node("press_release_writer", press_release_writer)
workflow.add_node("recipient_search", recipient_search)
workflow.add_node("email_distributor", email_distributor)
workflow.add_node("social_media_poster", social_media_poster)

# Define the workflow sequence
workflow.add_edge("press_release_writer", "recipient_search")
workflow.add_edge("recipient_search", "email_distributor")
workflow.add_edge("email_distributor", "social_media_poster")

# Set the entry point of the workflow
workflow.set_entry_point("press_release_writer")

# Compile the workflow graph
app = workflow.compile()

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
        st.session_state.state = press_release_writer(st.session_state.state)

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
                st.session_state.state = press_release_writer(st.session_state.state)
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