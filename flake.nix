{
  description = "Staffing GraphRAG";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
  };

  outputs =
    { nixpkgs, ... }:
    let
      inherit (nixpkgs) lib;
      forAllSystems = lib.genAttrs lib.systems.flakeExposed;
    in
    {
      devShells = forAllSystems (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};

          # Native dependencies for WeasyPrint
          weasyLibs = [
            pkgs.cairo
            pkgs.pango
            pkgs.gdk-pixbuf
            pkgs.harfbuzz
            pkgs.freetype
            pkgs.libffi
            pkgs.libjpeg
            pkgs.fontconfig
          ];

          openCVLibs = [
            pkgs.xorg.libX11
            pkgs.xorg.libXrender
            pkgs.xorg.libXext
            pkgs.xorg.libXcursor
            pkgs.xorg.libXrandr
            pkgs.xorg.libXinerama
            pkgs.libxcb
            pkgs.mesa
          ];

          # Manylinux-compatible runtime set (useful for binary wheels)
          manylinuxLibs = pkgs.pythonManylinuxPackages.manylinux1;
        in
        {
          default = pkgs.mkShell {
            packages = [
              pkgs.python312
              pkgs.uv
            ];

            env = lib.optionalAttrs pkgs.stdenv.isLinux {
              LD_LIBRARY_PATH = lib.makeLibraryPath (weasyLibs ++ openCVLibs ++ [ pkgs.stdenv.cc.cc.lib ]);
            };

            shellHook = ''
              cd backend
              uv sync
              . .venv/bin/activate
              cd ..
            '';
          };

          backend = pkgs.mkShell {
            packages = [
              pkgs.python312
              pkgs.uv
            ];

            env = lib.optionalAttrs pkgs.stdenv.isLinux {
              LD_LIBRARY_PATH = lib.makeLibraryPath (weasyLibs ++ openCVLibs ++ [ pkgs.stdenv.cc.cc.lib ]);
            };

            shellHook = ''
              cd backend
              uv sync
              . .venv/bin/activate
            '';
          };

          client = pkgs.mkShell {
            packages = [
              pkgs.python312
              pkgs.uv
            ];

            env = lib.optionalAttrs pkgs.stdenv.isLinux {
              LD_LIBRARY_PATH = lib.makeLibraryPath ([ pkgs.stdenv.cc.cc.lib ]);
            };

            shellHook = ''
              cd client
              uv sync
              . .venv/bin/activate
            '';
          };

          shared = pkgs.mkShell {
            packages = [
              pkgs.python312
              pkgs.uv
            ];

            env = lib.optionalAttrs pkgs.stdenv.isLinux {
              LD_LIBRARY_PATH = lib.makeLibraryPath ([ pkgs.stdenv.cc.cc.lib ]);
            };

            shellHook = ''
              cd shared
              uv sync
              . .venv/bin/activate
            '';
          };
        }
      );
    };
}
