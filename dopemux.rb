# Homebrew Formula for Dopemux
# 
# To install (after release):
#   brew install dopemux/tap/dopemux
# 
# To test locally:
#   brew install --build-from-source ./dopemux.rb
#

class Dopemux < Formula
  desc "ADHD-optimized development platform with AI-powered tools"
  homepage "https://github.com/dopemux/dopemux-mvp"
  url "https://github.com/dopemux/dopemux-mvp/archive/refs/tags/v0.1.0.tar.gz"
  sha256 "3dff7b728a8fe7330f25753cf1bd6185152aea3c694353be19dee93e8f8df8f8"
  license "MIT"
  head "https://github.com/dopemux/dopemux-mvp.git", branch: "main"
  
  # System dependencies
  depends_on "python@3.10"
  depends_on "git"
  depends_on "tmux"
  depends_on "jq"
  depends_on "curl"
  depends_on "sqlite"
  
  # Docker is optional (recommended but not required)
  depends_on "docker" => :optional
  
  # Python dependencies (installed via pip in virtualenv)
  resource "requirements" do
    url "https://raw.githubusercontent.com/dopemux/dopemux-mvp/main/requirements.txt"
    sha256 "PLACEHOLDER_REQUIREMENTS_SHA256"
  end
  
  def install
    # Install everything to libexec to avoid conflicts
    libexec.install Dir["*"]
    
    # Create Python virtualenv
    virtualenv_create(libexec, "python3.10")
    
    # Install Python dependencies
    system libexec/"bin/pip", "install", "-r", libexec/"requirements.txt"
    
    # Create dopemux wrapper script
    (bin/"dopemux").write <<~EOS
      #!/bin/bash
      export DOPEMUX_HOME="${HOME}/.dopemux"
      export PATH="#{libexec}/bin:$PATH"
      exec "#{libexec}/install.sh" "$@"
    EOS
    
    # Make wrapper executable
    chmod 0755, bin/"dopemux"
    
    # Create info file
    (prefix/"info.txt").write <<~EOS
      Dopemux has been installed!
      
      To complete setup, run:
        dopemux --quick
      
      For full installation:
        dopemux --full
      
      Documentation:
        https://github.com/dopemux/dopemux-mvp
    EOS
  end
  
  def post_install
    # Create dopemux home directory
    (var/"dopemux").mkpath
    
    # Print instructions
    ohai "Dopemux installed successfully!"
    puts <<~EOS
      
      Next steps:
      1. Run: dopemux --quick     (for core setup)
      2. Or:  dopemux --full      (for complete setup)
      
      Configuration will be stored in: ~/.dopemux
      
      For help: dopemux --help
    EOS
  end
  
  test do
    # Test that the wrapper script exists and is executable
    assert_predicate bin/"dopemux", :exist?
    assert_predicate bin/"dopemux", :executable?
    
    # Test help output
    assert_match "Usage:", shell_output("#{bin}/dopemux --help")
    
    # Test version/verify (non-interactive)
    system bin/"dopemux", "--verify"
  end
  
  def caveats
    <<~EOS
      Dopemux requires Docker for full functionality.
      
      If Docker is not installed:
        brew install --cask docker
      
      After installation, run:
        dopemux --quick
      
      To start services:
        dopemux start
    EOS
  end
end
