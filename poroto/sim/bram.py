from ..common import load_template
from ..config import gen_path, src_path
from ..memory import Memory
from pycparser import c_ast
from ..common import get_bit_width
import string
import os

class BramMemory(Memory):
    def get_component(self):
        return ["signal %s_addra : std_logic_vector(%d-1 downto 0);" % (self.name, self.address_size),
                "signal %s_addrb : std_logic_vector(%d-1 downto 0);" % (self.name, self.address_size),
                ]
    def get_instance(self):
        return ["%s_i : bram" % self.name,
                "generic map (",
                "DATA => %d," % self.data_size,
                "ADDR => %d" % self.address_size,
                ")",
                "port map(",
                "-- Port A",
                "clka   => clk,",
                "--rsta",
                "--ena",
                "wea    => bram_mem_m2s(%d).we," % self.index,
                "addra  => %s_addra," % (self.name),
                "dina   => bram_mem_m2s(%d).din," % self.index,
                "douta  => bram_mem_s2m(%d).dout," % self.index,

                "-- Port B",
                "clkb  => clk,",
                "--rstb",
                "--enb",
                "web    => bram_app_m2s(%d).we," % self.index,
                "addrb  => %s_addrb," % (self.name),
                "dinb   => bram_app_m2s(%d).din," % self.index,
                "doutb  => bram_app_s2m(%d).dout" % self.index,
                ");",
                "%s_addra  <= bram_mem_m2s(%d).addr_w(%d-1 downto 0) when bram_mem_m2s(%d).we = '1' else bram_mem_m2s(%d).addr_r(%d-1 downto 0);" % (self.name, self.index, self.address_size, self.index, self.index, self.address_size),
                "%s_addrb  <= bram_app_m2s(%d).addr_w(%d-1 downto 0) when bram_app_m2s(%d).we = '1' else bram_app_m2s(%d).addr_r(%d-1 downto 0);" % (self.name, self.index, self.address_size, self.index, self.index, self.address_size),
                ]
    def generate(self, designer):
        designer.add_file(src_path, "bram.vhdl")

class BromMemory(Memory):
    def __init__(self, name, data_type, size, init, debug):
        Memory.__init__(self, name, data_type, size, init, debug)
        self.brom_template = load_template('brom.vhdl')

    def generate(self, designer):
        out = open(os.path.join(gen_path, 'vhdl', "%s_brom.vhdl" % self.name), 'w' )
        for line in self.brom_template:
            if '%%%NAME%%%' in line:
                line = string.replace(line, '%%%NAME%%%', self.name + "_brom")
            if '%%%SIZE%%%' in line:
                line = string.replace(line, '%%%SIZE%%%', str(self.size))
            if '%%%ADDR_LEN%%%' in line:
                line = string.replace(line, '%%%ADDR_LEN%%%', str(get_bit_width(self.size)))
            if '%%%DATA_SIZE%%%' in line:
                line = string.replace(line, '%%%DATA_SIZE%%%', str(self.data_size))
            if '%%%DATA%%%' in line:
                for (i, value) in enumerate(reversed(self.init.exprs)):
                    if isinstance(value, c_ast.UnaryOp):
                        value = "-%s" % value.expr.value
                    else:
                        value = value.value
                    print >> out, "\t  std_logic_vector(to_unsigned(%s, 32))%s" % (value, ',' if i < len(self.init.exprs) - 1 else '')
                continue
            print >> out, line,
        designer.add_file(gen_path, "%s_brom.vhdl" % self.name)
        out.close()
