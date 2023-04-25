from setuptools import Extension
from setuptools.command.build_ext import build_ext
import subprocess
import platform
import sys

import os 
import re

HOMEDIR = os.getcwd()

def getPackageVersion():
    __version__ = re.findall(
        r"""__version__ = ["']+([0-9\.]*)["']+""",
        open('ICARUS/__init__.py').read(),
    )[0]

class repository():
    def __init__(self, name, url, MakeType):
        self.url = url
        self.name = name
        self.type = MakeType

    def clone(self):
        # Clone the repository
        self.repoDir = os.path.join(HOMEDIR,'3d_Party', self.name)
        clone_cmd = f'git clone {self.url} {self.repoDir}'
        try:
            subprocess.call(clone_cmd.split())
        except:
            print(f'Failed to clone {self.name} repository. Please make sure git is installed and try again.')

class BuildExtension(Extension):
    def __init__(self, name, make_list_dir, makeType,configire_commands, **kwargs):
        super().__init__(name, sources=[], **kwargs)
        self.make_lists_dir = os.path.abspath(make_list_dir)
        self.type = makeType
        self.configire_commands = configire_commands

class MakeBuild(build_ext):
    def build_extensions(self):
        for ext in self.extensions:
            extdir = os.path.abspath(os.path.dirname(self.get_ext_fullpath(ext.name)))
            cfg = 'Release'

            if ext.type == "CMake":
                # Ensure that CMake is present and working
                try:
                    out = subprocess.check_output(['cmake', '--version'])
                except OSError:
                    raise RuntimeError('Cannot find CMake executable')
                cmake_args = [
                    '-DCMAKE_BUILD_TYPE=%s' % cfg,
                    # Ask CMake to place the resulting library in the directory containing the extension
                    '-DCMAKE_LIBRARY_OUTPUT_DIRECTORY_{}={}'.format(cfg.upper(), extdir),
                    # Other intermediate static libraries are placed in a temporary build directory instead
                    '-DCMAKE_ARCHIVE_OUTPUT_DIRECTORY_{}={}'.format(cfg.upper(), self.build_temp),
                    # Hint CMake to use the same Python executable that is launching the build, prevents possible mismatching if
                    # multiple versions of Python are installed
                    '-DPYTHON_EXECUTABLE={}'.format(sys.executable),
                ]
                # We can handle some platform-specific settings at our discretion
                if platform.system() == 'Windows':
                    plat = ('x64' if platform.architecture()[0] == '64bit' else 'Win32')
                    cmake_args += [
                        # These options are likely to be needed under Windows
                        '-DCMAKE_WINDOWS_EXPORT_ALL_SYMBOLS=TRUE',
                        '-DCMAKE_RUNTIME_OUTPUT_DIRECTORY_{}={}'.format(cfg.upper(), extdir),
                    ]
                    # Assuming that Visual Studio and MinGW are supported compilers
                    if self.compiler.compiler_type == 'msvc':
                        cmake_args += [
                            '-DCMAKE_GENERATOR_PLATFORM=%s' % plat,
                            ]
                    else:
                        cmake_args += [
                            '-DCMAKE_CXX_COMPILER=g++' ,
                            '-DCMAKE_C_COMPILER=gcc',
                            '-DCMAKE_FORTRAN_COMPILER=gfortran',
                            '-G', 'MinGW Makefiles',
                        ]

                if not os.path.exists(self.build_temp):
                    os.makedirs(self.build_temp)

                # Config and build the extension
                subprocess.check_call(['cmake', ext.make_lists_dir] + cmake_args, cwd=self.build_temp)
                subprocess.check_call(['cmake', '--build', '.', '--config', cfg], cwd=self.build_temp)

            elif ext.type == "make":
                # Run the MAKE command
                if platform.system() == 'Windows':
                    make_cmd = f'mingw32-make.exe'
                else:
                    make_cmd = f'make'

                if not os.path.exists(self.build_temp):
                    os.makedirs(self.build_temp)
                print(ext.make_lists_dir)
                subprocess.check_call([make_cmd, 'gnu'], cwd=ext.make_lists_dir)
                
            elif ext.type == 'pip':
                pass
            else:
                print(f"Dont know how to make type {ext.type}")

repos = {
    'CGNS': {
        'url': 'https://github.com/CGNS/CGNS.git',
        'configure_commands': [],
        'type': "CMake"
        },
    'structAirfoilMesher': {
        'url': 'https://gitlab.com/before_may/structAirfoilMesher.git',
        'configure_commands': [],
        'type': "make"
        },
}

def main():
    ext_modules = []
    for repo in repos.keys():
        repo = repository(repo, repos[repo]['url'], repos[repo]['type'])
        # repo.clone()
        ext_modules.append(BuildExtension(name = repo.name, make_list_dir = repo.repoDir, makeType= repo.type ))

    __version__ = getPackageVersion()

    # Should Check for intel fortran, opemmpi, mlk

    # Command line flags forwarded to CMake
    if len(sys.argv) >= 2:
        command = sys.argv[1]
    else:
        command = 'install'

    package = "ICARUS"
    if command == 'install':
        install(package, __version__)
    elif command == 'uninstall':
        uninstall(package)
    else:
        print("Command not recognized")
        print("Usage: python setup.py [install|uninstall]")
        sys.exit(1)

def install(package,version):
    try:
        from setuptools import setup
    except ImportError:
        print("Please install setuptools")
    setup(
        name = package,
        version= version,
        # ext_modules= ext_modules,
        # cmdclass={'build_ext': MakeBuild},
    )

def uninstall(package):
    try:
        import pip
    except ImportError:
        print("Error importing pip")
    pip.main(['uninstall', package, '-y'])

if __name__ == "main":
    main()