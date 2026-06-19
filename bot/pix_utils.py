"""
PIX Utils — Gera payload BR Code + QR Code para pagamentos PIX.
Padrão EMVCo / BACEN — compatível com qualquer banco brasileiro.
"""

import crcmod
import qrcode
from io import BytesIO


# ---------- CONFIGURAÇÃO PIX ----------
PIX_KEY = "+5521985476700"
MERCHANT_NAME = "Albrecht Guilherme Nascimento Duwe"
MERCHANT_CITY = "Rio de Janeiro"

# Planos
PLANOS_PIX = {
    "basico":  {"nome": "Plano Basico EnglishFlow", "valor": 30.00},
    "pro":     {"nome": "Plano Pro EnglishFlow",     "valor": 55.00},
    "premium": {"nome": "Plano Premium EnglishFlow",  "valor": 80.00},
}


# ---------- PIX BR CODE ----------

def _crc16(payload: str) -> str:
    """Calcula CRC16-CCITT (0xFFFF) do payload PIX — padrão BACEN."""
    # BACEN PIX: CRC16-CCITT com valor inicial 0xFFFF
    # Polynomial 0x1021, init=0xFFFF, sem reflexão, sem XOR final
    crc_func = crcmod.mkCrcFun(0x11021, initCrc=0xFFFF, rev=False, xorOut=0x0000)
    crc = crc_func(payload.encode("ascii"))
    return f"{crc:04X}"


def _format_tlv(tag: str, value: str) -> str:
    """Formata campo TLV (Tag-Length-Value)."""
    length = f"{len(value):02d}"
    return f"{tag}{length}{value}"


def _format_merchant_account(key: str) -> str:
    """Campo 26 — Merchant Account Information (GUI)."""
    gui = _format_tlv("00", "br.gov.bcb.pix")  # GUI
    gui += _format_tlv("01", key)               # Chave PIX
    return _format_tlv("26", gui)


def generate_pix_payload(valor: float, descricao: str = "") -> str:
    """
    Gera a string completa do PIX BR Code.
    Args:
        valor: valor em reais (ex: 30.00)
        descricao: descrição opcional (aparece no comprovante)
    Returns:
        String do BR Code copia-e-cola.
    """
    payload = ""
    # 00 — Payload Format Indicator (fixo)
    payload += _format_tlv("00", "01")
    # 26 — Merchant Account Information (chave PIX)
    payload += _format_merchant_account(PIX_KEY)
    # 52 — Merchant Category Code (fixo 0000)
    payload += _format_tlv("52", "0000")
    # 53 — Transaction Currency (986 = BRL)
    payload += _format_tlv("53", "986")
    # 54 — Transaction Amount
    payload += _format_tlv("54", f"{valor:.2f}")
    # 58 — Country Code
    payload += _format_tlv("58", "BR")
    # 59 — Merchant Name
    name = MERCHANT_NAME[:25]  # Máx 25 chars
    payload += _format_tlv("59", name)
    # 60 — Merchant City
    city = MERCHANT_CITY[:15]  # Máx 15 chars
    payload += _format_tlv("60", city)
    # 62 — Additional Data Field (REMOVED: alguns bancos rejeitam)

    # 63 — CRC16 (calculado sobre payload + "6304")
    payload += "6304"
    crc = _crc16(payload)
    payload += crc

    return payload


def generate_qr_bytes(valor: float, descricao: str = "") -> BytesIO:
    """
    Gera imagem PNG do QR Code PIX.
    Args:
        valor: valor em reais
        descricao: descrição opcional
    Returns:
        BytesIO contendo a imagem PNG.
    """
    payload = generate_pix_payload(valor, descricao)

    qr = qrcode.QRCode(
        version=None,  # auto
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(payload)
    qr.make(fit=True)

    img = qr.make_image(fill_color="#0F172A", back_color="#FFFFFF")
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


def get_plano_info(plano_id: str) -> dict | None:
    """Retorna info do plano ou None."""
    return PLANOS_PIX.get(plano_id)
