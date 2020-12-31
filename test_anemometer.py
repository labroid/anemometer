import time
import pytest
from anemometer import wind_data_from_bytes

# b'\x02Q,078,007.10,K,00,\x0311\r\n'
# Speed: 7.1, Direction: 78, Units: K, Status: 00
# b'\x02Q,083,007.22,K,00,\x0314\r\n'
# Speed: 7.22, Direction: 83, Units: K, Status: 00
# b'\x02Q,083,007.16,K,00,\x0313\r\n'
# Speed: 7.16, Direction: 83, Units: K, Status: 00
# b'\x02Q,081,007.47,K,00,\x0315\r\n'
# Speed: 7.47, Direction: 81, Units: K, Status: 00
# b'\x02Q,082,007.31,K,00,\x0317\r\n'
# Speed: 7.31, Direction: 82, Units: K, Status: 00


@pytest.mark.parametrize('bytes_in, ms, string_out, err_out',
                         [(b"\x02Q,078,007.10,K,00,\x0311\r\n", 1609388604192, '{"t": 1609388604192, "h": 78, "s": 7.1, "u": "K", "k": "00"}', False),
                          (b'\x02Q,083,007.22,K,00,\x0314\r\n', 1609388604192, '{"t": 1609388604192, "h": 83, "s": 7.22, "u": "K", "k": "00"}', False),
                          (b'\x05Q,083,007.22,K,00,\x0314\r\n', 1609388604192, '', True),  #Bad checksum
                          (b'\x02Q,083.33,007.22,K,00,\x033A\r\n', 1609388604192, '', True),  #Float instead of integer
                          (b'\x02Q,dog,007.22,K,00,\x0343\r\n', 1609388604192, '', True),  # String instead of integer
                          ])
def test_wind_data_from_bytes(bytes_in, ms, string_out, err_out):
    s, e = wind_data_from_bytes(bytes_in, ms)
    assert (
        s == string_out and bool(e) == err_out
    )
    print(f"s->{s}<-, e->{e}<-")
