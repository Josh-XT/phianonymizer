from llama_cpp import Llama
import json
import base64
from typing import Tuple, Dict, List
from dataclasses import dataclass
from cryptography.fernet import Fernet
import random


@dataclass
class PHIMapper:
    """Class to handle PHI mapping and encryption"""

    def __init__(
        self,
        key: bytes = None,
        phi_map: Dict[str, str] = {},
        reverse_map: Dict[str, str] = {},
        fernet: Fernet = None,
        gguf_repo_id: str = "bartowski/Qwen2.5-0.5B-Instruct-GGUF",
        filename: str = "*Q4_K_M.gguf",
        context_length: int = 32768,
    ):
        self.key = key if key else Fernet.generate_key()
        self.phi_map = phi_map if phi_map else {}
        self.reverse_map = reverse_map if reverse_map else {}
        self.fernet = fernet if fernet else Fernet(key)
        self.llm = Llama.from_pretrained(
            repo_id=(
                gguf_repo_id if gguf_repo_id else "bartowski/Qwen2.5-0.5B-Instruct-GGUF"
            ),
            filename=filename if filename else "*Q4_K_M.gguf",
            n_ctx=context_length if context_length else 32768,
            verbose=False,
        )

    @classmethod
    def create(cls) -> "PHIMapper":
        """Create a new PHIMapper instance with a fresh key"""
        key = Fernet.generate_key()
        return cls(key=key, phi_map={}, reverse_map={}, fernet=Fernet(key))

    @classmethod
    def from_key(cls, key: bytes) -> "PHIMapper":
        """Create a PHIMapper instance from an existing key"""
        return cls(key=key, phi_map={}, reverse_map={}, fernet=Fernet(key))

    def identify_and_replace_phi(self, text: str) -> Tuple[List[dict], Dict[str, str]]:
        """Identify PHI and generate replacements in a single LLM call"""
        # Count tokens in text

        prompt = f"""The assistant is a PHI identification and replacement suggestion expert.

Example input:
"Patient John Smith (DOB: 01/15/1980) lives at 123 Main St."

Example output:
{{
    "phi_items": [
        {{
            "phi": "John",
            "category": "first_name",
            "replacement": "Michael"
        }},
        {{
            "phi": "Smith",
            "category": "last_name",
            "replacement": "Johnson"
        }},
        {{
            "phi": "01/15/1980",
            "category": "date",
            "replacement": "03/22/1972"
        }},
        {{
            "phi": "123 Main St",
            "category": "location",
            "replacement": "456 Oak Ave"
        }},
        {{
            "phi": "Columbus, Ohio",
            "category": "location",
            "replacement": "Seattle, Washington"
        }}
        {{
            "phi": "123-45-6789",
            "category": "social_security_number",
            "replacement": "987-65-4321"
        }},
        {{
            "phi": "555-1234",
            "category": "phone_number",
            "replacement": "555-5678"
        }},
        {{
            "phi": "john.doe@gmail.com",
            "category": "email",
            "replacement": "superman@example.com"
        }}
    ]
}}

Here are some examples of what should be classified as PHI and replaced with some random other values:
- Names
- Dates (e.g. birth dates, admission dates)
- Locations (e.g. addresses, cities, states)
- Contact information (e.g. phone numbers, email addresses)
- Identifiers (e.g. Social Security numbers, patient ID numbers)
- Passwords or PIN numbers

- The "phi" section should include the exact PHI text as it appears in the input.
- The "replacement" section should provide a suggested replacement for the PHI that is not the same as the original, very different, and follows the rules below.

Categories are:
- name
- date
- location
- phone_number
- email
- social_security_number

Rules:
- Make a list of each piece of PHI exactly as it is written in the data provided. If it is written in multiple ways (e.g. "John Smith" and "J. Smith"), list each variation separately.
- For the "replacement", generate replacements that:
   - Match the original format exactly
   - Are clearly different from the original
   - Use common but not famous names
   - Use real city/state names but fake addresses
   - Use different city/state/provice names than the original
   - Don't use the same city name as the phi
   - Maintain date formats (MM/DD/YYYY)
   - Keep area code formats for phone numbers
   - Preserve ID/number patterns
   - Phone numbers should be very different with different area codes and all other numbers changed.
   - Phone numbers should not use the same first 6 digits as the original.
   - Phone numbers should not use the same last 4 digits as the original.
   - Use an ENTIRELY made up phone number for the replacement.
   - Email replacements should be generic and not linked to real domains, e.g., "test@example.com"
   - Only replace the PHI data and not any other text
   - Always replace PHI with something else that is not the same as the original
   - Never use the `phi` as the `replacement`! The replacement is the assistant's anonymized version of the `phi`.
   - Be creative with replacements, they should not be anything close to the original.
   - Dates must never be the same as the original date.
- The example only exists as an example and is NOT part of the data to analyze.
- Every "replacement" should be vastly different from the "phi" it is replacing and not even close to the same.
- The user's input is the data to analyze.
- The "phi_items" list should contain all identified PHI with their replacements.
- The "replacement" must never be the same as the "phi"!
- The "phi" should be the exact text of the PHI data that you have identified to be replaced with the "replacement".
- The "phi" section is only for the exact text of the PHI data that you have identified to be replaced with the "replacement", it is not the category or anything else.

The assistant is very strict about PHI safety and security. You are the assistant.

Analyze the text in data and respond with only valid JSON as shown in the example."""

        response = self.llm.create_chat_completion(
            messages=[
                {
                    "role": "system",
                    "content": prompt,
                },
                {
                    "role": "user",
                    "content": f"## Data:\n{text}\n\nGiven the text under Data, identify all PHI (Protected Health Information) and generate appropriate replacements that are not the same as the original, very different, and follow the rules below.",
                },
            ],
            response_format={
                "type": "json_object",
            },
            temperature=0.4,
            max_tokens=32768,
        )

        try:
            result = json.loads(response["choices"][0]["message"]["content"])
            phi_items = result.get("phi_items", [])
            for item in phi_items:
                if "category" not in item:
                    item["category"] = "other"
                if "replacement" not in item:
                    # randomly generate a replacement
                    item["replacement"] = "".join(
                        [chr(random.randint(97, 122)) for _ in range(10)]
                    )
                if item["category"] == "phone_number":
                    # Make a random 10 digit number
                    item["replacement"] = "".join(
                        [str(random.randint(0, 9)) for _ in range(10)]
                    )
                    # Add dashes in the middle
                    item["replacement"] = (
                        item["replacement"][:3]
                        + "-"
                        + item["replacement"][3:6]
                        + "-"
                        + item["replacement"][6:]
                    )
                if item["category"] == "date":
                    # Make a random date
                    item["replacement"] = (
                        f"{random.randint(1, 12)}/{random.randint(1, 31)}/{random.randint(1900, 2023)}"
                    )
            # print(f"Output: {json.dumps(phi_items, indent=2)}")
            # Create replacement mapping
            replacements = {item["phi"]: item["replacement"] for item in phi_items}
            return phi_items, replacements

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            print(f"Output: {response['choices'][0]['message']['content']}")
            print(f"Error parsing LLM output: {e}")
            return [], {}

    def anonymize(self, text: str) -> str:
        """Anonymize text by replacing PHI with generated replacements"""
        # Get PHI items and replacements
        token_ids = self.llm.tokenize(text.encode("utf-8"))
        num_tokens = len(token_ids)

        phi_items = []
        replacements = {}
        if num_tokens > 32768:
            print(f"Number of tokens {num_tokens} > 32768, splitting into 16k chunks")
            for i in range(0, num_tokens, 16384):
                chunk = token_ids[i : i + 16384]
                chunk_data = self.llm.detokenize(chunk)
                phi_items_chunk, replacements_chunk = self.identify_and_replace_phi(
                    chunk_data
                )
                phi_items.extend(phi_items_chunk)
                replacements.update(replacements_chunk)
        else:
            phi_items, replacements = self.identify_and_replace_phi(text)

        if not phi_items:
            return text

        # Update the mapping dictionaries
        for item in phi_items:
            original = item["phi"]
            replacement = item["replacement"]
            self.phi_map[original] = replacement
            self.reverse_map[replacement] = original

        # Sort items by length (descending) to handle overlapping items correctly
        sorted_items = sorted(phi_items, key=lambda x: len(x["phi"]), reverse=True)

        # Apply replacements
        anonymized = text
        for item in sorted_items:
            anonymized = anonymized.replace(item["phi"], item["replacement"])

        return anonymized

    def deanonymize(self, text: str) -> str:
        """Restore original PHI from anonymized text"""
        deanonymized = text

        # Sort tokens by length (descending) to handle overlapping tokens correctly
        tokens = sorted(self.reverse_map.keys(), key=len, reverse=True)

        for token in tokens:
            if token in deanonymized:
                deanonymized = deanonymized.replace(token, self.reverse_map[token])
        # TODO: Dates might be in different format, so we need to handle them differently
        # Considering a second pass to the local LLM to identify incorrectly replaced data and offer new replacements with the original text in context
        # If we give it the mapping and tell it to build a new replacement mapping based on the current text vs the mapping it has, we can get a better result
        return deanonymized

    def export_encrypted_map(self) -> str:
        """Export the PHI mapping in an encrypted format"""
        map_data = {"phi_map": self.phi_map, "reverse_map": self.reverse_map}
        encrypted_data = self.fernet.encrypt(json.dumps(map_data).encode())
        return base64.b64encode(encrypted_data).decode()

    def import_encrypted_map(self, encrypted_map: str) -> None:
        """Import an encrypted PHI mapping"""
        encrypted_data = base64.b64decode(encrypted_map)
        decrypted_data = self.fernet.decrypt(encrypted_data)
        map_data = json.loads(decrypted_data)
        self.phi_map = map_data["phi_map"]
        self.reverse_map = map_data["reverse_map"]


def anonymize_text(
    text: str,
    model_repo: str = "bartowski/Qwen2.5-0.5B-Instruct-GGUF",
    model_filename: str = "*Q4_K_M.gguf",
) -> Tuple[str, PHIMapper]:
    """
    Main function to anonymize text containing PHI
    Returns anonymized text and PHIMapper instance
    """
    # Create new PHI mapper
    mapper = PHIMapper(
        gguf_repo_id=model_repo,
        filename=model_filename,
    ).create()

    # Anonymize the text
    anonymized_text = mapper.anonymize(text)

    return anonymized_text, mapper


def deanonymize_text(text: str, mapper: PHIMapper) -> str:
    """
    Main function to deanonymize text using a PHIMapper
    """
    return mapper.deanonymize(text)
