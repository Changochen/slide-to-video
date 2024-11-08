from typing import Optional, List, Tuple
from docx import Document
import re
from dataclasses import dataclass


class ScriptConfig(dict):
    pass


@dataclass
class Script:
    text: str
    original_text: str
    path: str
    config: Optional[ScriptConfig] = None


def extract_text_from_docx(file_path):
    """
    Extracts all the text from a Word document (.docx).

    Parameters:
    file_path (str): The path to the Word document file.

    Returns:
    str: The extracted text.
    """
    doc = Document(file_path)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return "\n".join(full_text)


class ScriptEngine:
    def load_script(self, script_path) -> str:
        script_path = str(script_path)
        if script_path.endswith(".docx") or script_path.endswith(".doc"):
            return extract_text_from_docx(script_path)
        else:
            with open(script_path, "r") as f:
                return f.read()

    def parse_script(self, script) -> Tuple[str, Optional[ScriptConfig]]:
        lines = script.split("===")
        script_text = lines[0].strip()
        if len(lines) == 1:
            return script_text, None
        config = ScriptConfig()
        if len(lines) != 2:
            raise ValueError("Invalid script format")
        config_text = lines[1].strip()
        for line in config_text.split("\n"):
            key, value = line.split(":")
            if key.strip() == "#delay":
                config["delay"] = float(value.strip())
        return script_text, config

    def split_script(
        self, script_path, output_path: str, *, marker="NEWSLIDE", script_dict=None
    ) -> List[Script]:
        text = self.load_script(script_path)
        sub_paragraphs = text.split(marker)
        script_paths = []
        for sub_paragraph in sub_paragraphs:
            if sub_paragraph.strip():
                original_text, script_config = self.parse_script(sub_paragraph)
                replaced_text = original_text
                output_file = f"{output_path}/sub_paragraph_{len(script_paths)+1}.txt"
                if script_dict:
                    replaced_text = self.replace_dict(original_text, script_dict)
                with open(output_file, "w") as f:
                    f.write(replaced_text)
                script_paths.append(
                    Script(
                        text=replaced_text,
                        original_text=original_text,
                        path=output_file,
                        config=script_config,
                    )
                )

        return script_paths

    def replace_dict(self, text, replace_dict):
        for original_text, new_text in replace_dict.items():
            # If the orginal text, which is a word, is in the text, replace it with the new text
            # Look for the word, it should be surrounded by non alphanumeric characters.
            # This is to avoid replacing substrings.
            text = re.sub(rf"\b{original_text}\b", new_text, text)
            # If the original text is a plural word, replace the singular form as well
            text = re.sub(rf"\b{original_text + 's'}\b", new_text + "s", text)
        return text
