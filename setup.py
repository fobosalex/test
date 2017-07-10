from distutils.core import setup
import py2exe

setup(
    service = ["svpysvc"],
    description = "Supervisor service for listed in cofig processes",
    modules = ["SVPySvc"],
    cmdline_style='pywin32',
)