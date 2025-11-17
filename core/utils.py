# core/utils.py
from math import floor

UNIDADES = (
    '', 'UNO', 'DOS', 'TRES', 'CUATRO', 'CINCO', 'SEIS', 'SIETE', 'OCHO', 'NUEVE',
    'DIEZ', 'ONCE', 'DOCE', 'TRECE', 'CATORCE', 'QUINCE', 'DIECISÉIS', 'DIECISIETE', 'DIECIOCHO', 'DIECINUEVE'
)
DECENAS = (
    '', '', 'VEINTE', 'TREINTA', 'CUARENTA', 'CINCUENTA', 'SESENTA', 'SETENTA', 'OCHENTA', 'NOVENTA'
)
CENTENAS = (
    '', 'CIEN', 'DOSCIENTOS', 'TRESCIENTOS', 'CUATROCIENTOS', 'QUINIENTOS', 'SEISCIENTOS', 'SETECIENTOS', 'OCHOCIENTOS', 'NOVECIENTOS'
)

def _convertir_menor_1000(n):
    assert 0 <= n < 1000
    centenas = n // 100
    resto = n % 100
    resultado = ''
    if centenas:
        if centenas == 1 and resto == 0:
            return 'CIEN'
        resultado += CENTENAS[centenas]
        if resto:
            resultado += ' '
    if resto < 20:
        resultado += UNIDADES[resto]
    else:
        dec = resto // 10
        uni = resto % 10
        if dec == 2 and uni != 0:
            # VEINTIUNO, VEINTIDÓS (sin espacio)
            resultado += 'VEINTI' + UNIDADES[uni].lower()
            resultado = resultado.upper()
        else:
            resultado += DECENAS[dec]
            if uni:
                resultado += ' Y ' + UNIDADES[uni]
    return resultado.strip()

def numero_a_letras(num):
    """
    Convierte número (int) a letras en español (soporta hasta miles de millones en este impl).
    """
    if num == 0:
        return 'CERO'
    partes = []
    millones = num // 1_000_000
    resto = num % 1_000_000
    miles = resto // 1000
    unidades = resto % 1000

    if millones:
        if millones == 1:
            partes.append('UN MILLÓN')
        else:
            partes.append(f"{_convertir_menor_1000(millones)} MILLONES")

    if miles:
        if miles == 1:
            partes.append('MIL')
        else:
            partes.append(f"{_convertir_menor_1000(miles)} MIL")

    if unidades:
        partes.append(_convertir_menor_1000(unidades))

    return ' '.join(partes).strip()

def monto_en_letras(amount):
    """
    amount: Decimal, float o string convertible. Devuelve texto en mayúsculas,
    ejemplo: 1234.56 -> "UN MIL DOSCIENTOS TREINTA Y CUATRO LEMPIRAS CON 56/100"
    """
    from decimal import Decimal, ROUND_DOWN
    a = Decimal(str(amount)).quantize(Decimal('0.01'), rounding=ROUND_DOWN)
    entero = int(a // 1)
    centavos = int((a - entero) * 100)
    texto_entero = numero_a_letras(entero)
    return f"{texto_entero} LEMPIRAS CON {centavos:02d}/100"
