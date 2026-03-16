"""
Cocotb testbench for tt_um_malik_mac_ripple
Wraps gate-level unsigned 8-bit MAC: acc = a*b + acc (ripple carry)

Includes all 64 verified test vectors from the original DSE testbench,
plus wrapper-specific tests for accumulation, clear, and edge cases.
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles

CMD_NOP       = 0b000
CMD_LOAD_A    = 0b001
CMD_LOAD_B_GO = 0b010
CMD_READ_LSB  = 0b011
CMD_READ_MSB  = 0b100
CMD_READ_OVF  = 0b101
CMD_CLEAR     = 0b110


async def reset_dut(dut):
    dut.rst_n.value = 0
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)


async def mac(dut, a, b):
    dut.ui_in.value = a & 0xFF
    dut.uio_in.value = CMD_LOAD_A
    await ClockCycles(dut.clk, 1)
    dut.ui_in.value = b & 0xFF
    dut.uio_in.value = CMD_LOAD_B_GO
    await ClockCycles(dut.clk, 1)
    dut.uio_in.value = CMD_NOP
    await ClockCycles(dut.clk, 1)


async def read_acc(dut):
    dut.uio_in.value = CMD_READ_LSB
    await ClockCycles(dut.clk, 1)
    lsb = int(dut.uo_out.value)
    dut.uio_in.value = CMD_READ_MSB
    await ClockCycles(dut.clk, 1)
    msb = int(dut.uo_out.value)
    dut.uio_in.value = CMD_READ_OVF
    await ClockCycles(dut.clk, 1)
    ovf = int(dut.uo_out.value) & 1
    dut.uio_in.value = CMD_NOP
    await ClockCycles(dut.clk, 1)
    return (ovf << 16) | (msb << 8) | lsb


async def clear(dut):
    dut.uio_in.value = CMD_CLEAR
    await ClockCycles(dut.clk, 1)
    dut.uio_in.value = CMD_NOP
    await ClockCycles(dut.clk, 1)


# All 64 original verified vectors: (a, b, c, y) where y = a*b + c
VECTORS = [
    (0xe4, 0xc7, 0x99d9, 0x14b15), (0x26, 0x31, 0x75fe, 0x07d44),
    (0x28, 0x0d, 0x343e, 0x03646), (0x36, 0x91, 0x5439, 0x072cf),
    (0xc2, 0x8a, 0x27f6, 0x0908a), (0x90, 0x37, 0xc1fb, 0x0e0eb),
    (0xf7, 0x68, 0x1352, 0x077aa), (0xd1, 0xbb, 0x29f7, 0x0c2a2),
    (0xe6, 0x06, 0x40c5, 0x04629), (0x90, 0x12, 0x3283, 0x03ca3),
    (0xda, 0x1c, 0x3cc6, 0x0549e), (0x7c, 0x8f, 0xf94c, 0x13e90),
    (0x47, 0xa2, 0x66af, 0x0939d), (0x18, 0x9e, 0x9947, 0x0a817),
    (0xf3, 0x11, 0x3a59, 0x04a7c), (0x4c, 0xc5, 0xd15c, 0x10bd8),
    (0x4d, 0x41, 0x3128, 0x044b5), (0x46, 0x56, 0x6fe5, 0x08769),
    (0x21, 0x2e, 0xf812, 0x0fe00), (0xbf, 0x25, 0xf27c, 0x10e17),
    (0xb0, 0xb4, 0x6b1a, 0x0e6da), (0x7e, 0xcf, 0x37d5, 0x09db7),
    (0xd3, 0xe3, 0xcd1d, 0x18836), (0x83, 0xbf, 0x3678, 0x09835),
    (0x09, 0x7e, 0x67c0, 0x06c2e), (0x2a, 0x3a, 0x15ef, 0x01f73),
    (0xb8, 0xfb, 0x2599, 0x0da01), (0xce, 0xae, 0x2682, 0x0b286),
    (0xdd, 0x99, 0xb6c2, 0x13ad7), (0x57, 0x3e, 0xe972, 0x0fe84),
    (0x87, 0xc1, 0x6886, 0x0ce4d), (0x8c, 0x9f, 0x7e52, 0x0d546),
    (0xc5, 0x4d, 0x5c82, 0x097c3), (0x36, 0x9d, 0xe73f, 0x1085d),
    (0xaf, 0x81, 0xbc8b, 0x114ba), (0x65, 0x43, 0x94f2, 0x0af61),
    (0xb7, 0x08, 0x87c1, 0x08d79), (0x92, 0x16, 0x1fe3, 0x02c6f),
    (0x1f, 0xe2, 0x136e, 0x02ecc), (0xfa, 0x75, 0x6978, 0x0dbba),
    (0x32, 0x3d, 0xf46e, 0x10058), (0xa0, 0x03, 0x4eaa, 0x0508a),
    (0x6c, 0x62, 0x1450, 0x03da8), (0x91, 0xe1, 0x883c, 0x107ad),
    (0x16, 0xdf, 0x939f, 0x0a6c9), (0x33, 0x6c, 0x791c, 0x08ea0),
    (0x17, 0xb0, 0x8add, 0x09aad), (0xd1, 0xac, 0xc7ef, 0x1545b),
    (0x4b, 0x4c, 0x30a8, 0x046ec), (0xe4, 0xab, 0xf3e5, 0x18c31),
    (0xc9, 0x26, 0xe291, 0x10067), (0x6b, 0xa8, 0x138a, 0x059c2),
    (0x70, 0x20, 0x99b7, 0x0a7b7), (0xb5, 0xe5, 0xde34, 0x1801d),
    (0x79, 0x6a, 0x300a, 0x06224), (0xdf, 0xe3, 0xd036, 0x195f3),
    (0x14, 0x36, 0x8b02, 0x08f3a), (0xe6, 0x4f, 0x99e6, 0x0e0e0),
    (0xfb, 0x7a, 0xbdfd, 0x1359b), (0x7e, 0x43, 0x1b98, 0x03c92),
    (0x30, 0x06, 0x98bc, 0x099dc), (0x88, 0x79, 0x2763, 0x067ab),
    (0x46, 0x50, 0xfab9, 0x11099), (0x81, 0xfd, 0x5961, 0x0d8de),
]


@cocotb.test()
async def test_reset(dut):
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)
    val = await read_acc(dut)
    assert val == 0, f"Not zero after reset: {val}"
    dut._log.info("PASS: reset")


@cocotb.test()
async def test_simple_multiply(dut):
    """3 * 4 = 12."""
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)
    await mac(dut, 3, 4)
    val = await read_acc(dut)
    assert val == 12, f"Expected 12, got {val}"
    dut._log.info("PASS: 3 * 4 = 12")


@cocotb.test()
async def test_accumulate(dut):
    """3*4 + 10*20 = 212."""
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)
    await mac(dut, 3, 4)
    await mac(dut, 10, 20)
    val = await read_acc(dut)
    assert val == 212, f"Expected 212, got {val}"
    dut._log.info("PASS: accumulation = 212")


@cocotb.test()
async def test_max_single(dut):
    """255 * 255 = 65025."""
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)
    await mac(dut, 255, 255)
    val = await read_acc(dut)
    assert val == 65025, f"Expected 65025, got {val}"
    dut._log.info("PASS: 255 * 255 = 65025")


@cocotb.test()
async def test_clear(dut):
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)
    await mac(dut, 100, 100)
    await clear(dut)
    val = await read_acc(dut)
    assert val == 0, f"After clear: expected 0, got {val}"
    dut._log.info("PASS: clear")


@cocotb.test()
async def test_zero_multiply(dut):
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)
    await mac(dut, 0, 255)
    val = await read_acc(dut)
    assert val == 0, f"0 * 255: expected 0, got {val}"
    dut._log.info("PASS: zero multiply")


@cocotb.test()
async def test_verified_products(dut):
    """Verify all 64 products from the original DSE testbench.

    Each vector has a*b+c=y, so a*b = y - c.
    We reset acc to 0 each time, compute mac(a,b), and check acc == a*b.
    """
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())

    passed = 0
    for i, (a, b, c, y) in enumerate(VECTORS):
        await reset_dut(dut)
        await mac(dut, a, b)
        val = await read_acc(dut)
        expected = (y - c) & 0x1FFFF
        assert val == expected, \
            f"Vec {i}: 0x{a:02x}*0x{b:02x} expected 0x{expected:05x}, got 0x{val:05x}"
        passed += 1

    dut._log.info(f"PASS: all {passed} verified product vectors")


@cocotb.test()
async def test_accumulator_chain(dut):
    """Test the feedback path: acc feeds back as the c input to the MAC."""
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # 3*4 = 12
    await mac(dut, 3, 4)
    val = await read_acc(dut)
    assert val == 12

    # 10*20 + 12 = 212
    await mac(dut, 10, 20)
    val = await read_acc(dut)
    assert val == 212

    # 255*1 + 212 = 467
    await mac(dut, 255, 1)
    val = await read_acc(dut)
    assert val == 467

    # 0*255 + 467 = 467 (zero preserves)
    await mac(dut, 0, 255)
    val = await read_acc(dut)
    assert val == 467

    dut._log.info("PASS: accumulator chain")


@cocotb.test()
async def test_overflow_bit(dut):
    """255*255 twice = 130050, bit 16 should be set."""
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    await mac(dut, 255, 255)  # 65025
    await mac(dut, 255, 255)  # 65025 + 65025 = 130050
    val = await read_acc(dut)
    assert val == 130050, f"Expected 130050, got {val}"
    assert (val >> 16) & 1 == 1, "Overflow bit not set"
    dut._log.info("PASS: overflow bit")
