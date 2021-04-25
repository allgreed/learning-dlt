let
  nixpkgs = builtins.fetchGit {
    name = "nixos-unstable-2020-09-26";
    url = "https://github.com/nixos/nixpkgs-channels/";
    ref = "refs/heads/nixos-unstable";
    rev = "daaa0e33505082716beb52efefe3064f0332b521";
    # obtain via `git ls-remote https://github.com/nixos/nixpkgs-channels nixos-unstable`
  };
  pkgs = import nixpkgs { config = {}; };
  pythonPkgs = python-packages: with python-packages; [
      ptpython # used for dev
      pytest # testing
      pytest-mock # testing
      pydantic
      ecdsa
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
