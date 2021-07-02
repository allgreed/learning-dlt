let
  nixpkgs = builtins.fetchGit {
    name = "nixos-unstable-2020-09-26";
    url = "https://github.com/nixos/nixpkgs-channels/";
    ref = "refs/heads/nixos-unstable";
    rev = "daaa0e33505082716beb52efefe3064f0332b521";
    # obtain via `git ls-remote https://github.com/nixos/nixpkgs-channels nixos-unstable`
  };
  pkgs = import nixpkgs { config = {}; };
  statemachine = pkgs.python38Packages.buildPythonPackage rec {
      pname = "python-statemachine";
      version = "0.8.0";

      src = pkgs.python38Packages.fetchPypi{
        inherit version;
        inherit pname;
        sha256 = "1bpbm68db4hviiprk4ypwrmid8cyxha93h7ahy21kcfq9qghr9zn";
      };

      doCheck = false;
  };
  pythonPkgs = python-packages: with python-packages; [
      ptpython # used for dev
      pytest # testing
      pytest-mock # testing
      pydantic
      ecdsa
      gmpy2
      statemachine
      python-language-server
    ];
  pythonCore = pkgs.python38;
  myPython = pythonCore.withPackages pythonPkgs;
in
pkgs.python3Packages.buildPythonApplication {
  pname = "main";
  src = ./.;
  version = "0.1";
  propagatedBuildInputs = [ myPython ];
}
