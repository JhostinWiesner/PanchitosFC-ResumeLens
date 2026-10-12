
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from core.catalog import Catalog, CatalogError
from pipeline import run
from profiles.dev_ops import DEVOPS
from profiles.full_stack import FULL_STACK
from profiles.ml_engineer import ML_ENGINEER
from profiles.data_engineer import DATA_ENGINEER


st.set_page_config(
    page_title="ResumeLens",
    page_icon="📄",
    layout="centered",
)

st.markdown(
    """
    <style>
        .block-container {
            max-width: 950px;
            padding-top: 2.5rem;
            padding-bottom: 3rem;
        }

        .app-subtitle {
            color: #666;
            margin-top: -0.5rem;
            margin-bottom: 2rem;
        }

        div[data-testid="stFileUploader"] {
            border-radius: 10px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("ResumeLens")
st.markdown(
    '<p class="app-subtitle">'
    "Evaluate a résumé against a professional profile."
    "</p>",
    unsafe_allow_html=True,
)

PROFILE_OPTIONS = {
    "Full Stack Developer": FULL_STACK,
    "Machine Learning Engineer": ML_ENGINEER,
    "DevOps Engineer": DEVOPS,
    "Data Engineer": DATA_ENGINEER,
}

uploaded_file = st.file_uploader(
    "Upload your résumé",
    type=["txt"],
    help="Upload a plain-text résumé encoded in UTF-8.",
)

selected_profile_name = st.selectbox(
    "Professional profile",
    options=list(PROFILE_OPTIONS.keys()),
)

if st.button("Evaluate résumé", type="primary", use_container_width=True):
    if uploaded_file is None:
        st.warning("Please upload a .txt résumé before evaluating.")
    else:
        try:
            resume_text = uploaded_file.getvalue().decode("utf-8-sig")

            if not resume_text.strip():
                st.warning("The uploaded file is empty.")
            else:
                catalog = Catalog.from_json()
                profile = PROFILE_OPTIONS[selected_profile_name]

                with st.spinner("Evaluating résumé..."):
                    result = run(resume_text, profile, catalog)

                st.session_state["resume_html"] = result.html_output
                st.session_state["resume_name"] = (
                    result.extracted.name or "candidate"
                )
                st.session_state["resume_profile"] = selected_profile_name
                st.session_state["resume_accepted"] = (
                    result.classification.accepted
                )

        except UnicodeDecodeError:
            st.error(
                "The file could not be read as UTF-8. "
                "Save the résumé as a UTF-8 .txt file and try again."
            )
        except (CatalogError, ValueError, KeyError) as error:
            st.error(f"Could not evaluate the résumé: {error}")
        except Exception as error:
            st.error(
                "An unexpected error occurred while evaluating the résumé. "
                f"Details: {error}"
            )

if st.session_state.get("resume_html"):
    st.divider()
    st.subheader("Evaluation result")

    if st.session_state["resume_accepted"]:
        st.success(
            f"Accepted for {st.session_state['resume_profile']}"
        )
    else:
        st.warning(
            f"Not accepted for {st.session_state['resume_profile']}"
        )

    html_output = st.session_state["resume_html"]

    components.html(
        html_output,
        height=1050,
        scrolling=True,
    )

    filename = (
        Path(st.session_state["resume_name"])
        .stem
        .strip()
        .replace(" ", "_")
        or "candidate"
    )

    st.download_button(
        label="Download candidate profile (HTML)",
        data=html_output.encode("utf-8"),
        file_name=f"{filename}_resume_profile.html",
        mime="text/html",
        use_container_width=True,
    )
