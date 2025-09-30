{
  description = "Kagi development flake";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.05";
  };

  outputs = { self, nixpkgs }:
    let
      systems = [
        "x86_64-linux"
        "aarch64-linux"
        "x86_64-darwin"
        "aarch64-darwin"
      ];
      forEachSystem = nixpkgs.lib.genAttrs systems;
    in {
      devShells = forEachSystem (system:
        let
          pkgs = import nixpkgs { inherit system; };
        in {
          default = pkgs.mkShell {
            packages = with pkgs; [
              python312
              uv
              zsh
            ];

            shellHook = ''
              # Keep uv-managed virtual environments local to this repo and align with nix python.
              export UV_PROJECT_ENV=".venv"
              export UV_PYTHON="${pkgs.python312}/bin/python3"
            '';
          };
        });
    };
}
