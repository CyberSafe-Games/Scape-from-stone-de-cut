"""Entrada compatível: o QA mobile agora valida a arte nativa, sem layout HTML."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from devtools.validate_web_mobile_art import main

if __name__=="__main__":
    main()
