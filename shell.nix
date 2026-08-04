{ pkgs ? import <nixpkgs> {}, system ? builtins.currentSystem, }:

let
  pinned = import (fetchTarball {
      name = "nixos-26.05";
      url = https://github.com/NixOS/nixpkgs/tarball/nixos-26.05;
  }) {};

  systemBuildExports = (
    with pinned;
    {
    x86_64-linux = ''
      export LD_LIBRARY_PATH=${pinned.stdenv.cc.cc.lib}/lib/:${pinned.zlib}/lib/:${pinned.postgresql.lib}/lib/:$LD_LIBRARY_PATH
    '';
    aarch64-darwin = ''
      export DYLD_LIBRARY_PATH=${pinned.stdenv.cc.cc.lib}/lib/:${pinned.zlib}/lib/:${pinned.postgresql.lib}/lib/:$DYLD_LIBRARY_PATH
    '';
    }
  );

in
  pkgs.mkShell {
    name = "projects.alembic-migration-linter";

    buildInputs = [
      pinned.autoPatchelfHook
      pinned.cmake
      pinned.coreutils
      pinned.direnv
      pinned.git
      pinned.gnumake
      pinned.poetry
      pinned.postgresql
      pinned.pre-commit
      pinned.python314
    ];

    nativeBuildInputs = [ pinned.autoPatchelfHook ];

    NIX_LDFLAGS = if system ? "x86_64-linux" then [ "-lstdc++"] else [];
    LANG="en_UK.UTF-8";

    shellHook = ''
      PATH="${pinned.poetry}:${pinned.python314}/bin:$PATH";
    '' + systemBuildExports.${system};
}
