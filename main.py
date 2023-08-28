import streamlit as st
from utils import pdfprocess
import pandas as pd


def process_text(session):
    """Process and format the input text."""
    input_txt = st.session_state[session]

    # Strip input_txt to remove leading/trailing whitespaces
    txt = input_txt.strip()

    # Replace newline characters and format punctuation
    txt = txt.replace("\n", " ").replace(". ", ".\n")

    # Handle exceptions
    for exc in ["Fig", "et al"]:
        txt = txt.replace(f"{exc}.\n", f"{exc}. ")

    txt = txt.replace(": ", ":\n")

    # Remove extra spaces
    while "  " in txt:
        txt = txt.replace("  ", " ")

    # Further process the text based on session's level
    processed_txt = pdfprocess.split_text_at_period(
        txt, st.session_state['level'])
    txt = "\n".join(processed_txt)

    st.session_state[session] = txt


def create_outline_from_fulltext(mds):
    """Create outline from the preprocessed fulltext."""
    sections = mds.split("# ")
    # 첫 번째 요소는 종종 빈 문자열이거나 시작 전 정보이므로 제외합니다.
    return [section.split('\n', 1)[0] for section in sections[1:]]


def processing_pdf(file):
    """Process the uploaded PDF and display its contents."""
    if 'outline_mode' not in st.session_state:
        st.session_state['outline_mode'] = False
    mds, outline = pdfprocess.process_pdf(file)

    if st.session_state['outline_mode'] == True:
        outline = create_outline_from_fulltext(mds)

    tab1, tab2, = st.tabs(["Preprocessed", "Markdown Preview"])

    with tab1:
        with st.sidebar:
            # Initialize or update 'level' and 'prev_level'
            st.session_state.setdefault('level', 200)
            st.session_state.setdefault(
                'prev_level', st.session_state['level'])

            st.session_state['level'] = st.slider(
                'Paragraph justification (specify character count)', 0, 2000, st.session_state['level'])

            st.session_state.setdefault('abstract', 'abstract')

            # Check if the slider value has changed and if so, update all text areas
            if st.session_state['prev_level'] != st.session_state['level']:
                # Update the abstract
                process_text('abstract')

                # Update all other text areas
                for line in outline:
                    process_text(line)

                # Update the prev_level to current level
                st.session_state['prev_level'] = st.session_state['level']

            st.text_area(str('Abstract'), height=200,
                         on_change=process_text, args=['abstract'], key='abstract',
                         help=f"Number of characters : {len(st.session_state['abstract'])}")

            # Create or update text areas based on the outline
            for i, line in enumerate(outline):
                # line[0]이 숫자인 경우
                if line[0].isdigit():
                    line = line.split(' ')[1:]
                    line = ' '.join(line)

                text_area_label = f" {line}" if i < len(
                    outline) - 1 else f" {line}"
                st.text_area(text_area_label, value=st.session_state.get(line, ""), on_change=process_text, args=[line],
                             height=200, key=line, help=f"Number of characters : {len(st.session_state.get(line, ''))}")

            # Handle custom text areas
            st.session_state.setdefault('custom_text_areas', [])

            for text_key, label in st.session_state['custom_text_areas']:
                st.session_state.setdefault(text_key, '')
                st.text_area(label,
                             value=st.session_state[text_key],
                             on_change=process_text,
                             args=[text_key],
                             height=200,
                             key=text_key)
                if st.button(f"Delete {label}", key=f"delete_{text_key}"):
                    del st.session_state[text_key]
                    st.session_state['custom_text_areas'].remove(
                        (text_key, label))
                    st.experimental_rerun()

            # Input for custom label
            custom_label = st.text_input("Enter Paragraph Name:")

            if st.button("Add Text Area with Custom Label"):
                if custom_label:  # Check if label is not empty
                    new_key = f"custom_text_area_{len(st.session_state['custom_text_areas']) + 1}"
                    st.session_state['custom_text_areas'].append(
                        (new_key, custom_label))
                    st.session_state[new_key] = ""
                    st.experimental_rerun()

            if st.button("Create Outline"):
                # Check if the outline was already created
                if not st.session_state['custom_text_areas']:
                    for line in outline:
                        new_key = f"outline_text_area_{line}"
                        st.session_state['custom_text_areas'].append(
                            (new_key, line))
                        st.session_state[new_key] = line
                    st.session_state['outline_mode'] = True
                    st.experimental_rerun()

        st.markdown(mds, unsafe_allow_html=True)

    with tab2:
        # Add the abstract label and content
        full_text = "# Abstract\n" + st.session_state['abstract'] + "\n\n"

        for i, line in enumerate(outline):
            # Create the markdown label for each section
            section_label = f"## {i + 1}. {line}"

            # Concatenate the markdown label with its respective content
            full_text += section_label + "\n" + st.session_state[line] + "\n\n"

        # 사용자가 직접 추가한 text_area의 내용도 마크다운 프리뷰에 포함
        for idx, (text_key, label) in enumerate(st.session_state['custom_text_areas']):
            # Create the markdown label for custom sections
            custom_section_label = f"## {label}"

            # Concatenate the markdown label with its respective content
            full_text += custom_section_label + "\n" + \
                st.session_state[text_key] + "\n\n"

        # Add download button for the markdown text
        st.download_button(
            label="download markdown",
            data=full_text.encode(),
            file_name="document.md",
            mime="text/markdown"
        )

        # Display the concatenated markdown text
        st.markdown(full_text, unsafe_allow_html=True)


def main():
    """Main Streamlit app."""
    st.set_page_config(layout="centered")
    st.title("PDF file upload")

    if st.button("Reload"):
        st.experimental_rerun()

    uploaded_file = st.file_uploader("select PDF File.", type=["pdf"])
    st.header('PDF Prompt(English)')
    st.code("""
            Given the text of a research paper, please return the text with the following modifications:
            Any mathematical formulas should be wrapped with $$ at the beginning and end of the formula.
            Correct any inconsistencies in paragraph spacing to ensure the text flows smoothly.
            Input Text: [Your research paper text here]
            """, language='python')
    st.header('PDF Prompt(Korean)')
    st.code("""
            Based on the text of the given research paper, please return it with the following corrections:

            Please wrap mathematical formulas so that they begin with $$ and end with $$.
            Fix any inconsistencies in paragraph spacing to make the text flow smoothly.
            Please translate the corrected text into Korean.
            Input text: [Enter thesis text]
            """, language='python')

    if uploaded_file:
        processing_pdf(uploaded_file)


if __name__ == "__main__":
    main()
