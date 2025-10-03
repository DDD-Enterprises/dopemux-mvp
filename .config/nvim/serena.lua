-- Serena v2 Auto-Activation for Neovim
--
-- Place this in your init.lua or source it with:
--   require('serena')
--
-- This will automatically start Serena v2 when you open a workspace

local M = {}

-- Configuration
M.config = {
  -- Path to auto-activator script (relative to workspace root)
  activator_path = "services/serena/v2/auto_activator.py",

  -- Auto-start on VimEnter
  auto_start = true,

  -- Log file location
  log_file = vim.fn.expand("~/.serena/neovim.log")
}

-- Start Serena v2 auto-activator in background
function M.start()
  local workspace_root = vim.fn.getcwd()
  local activator_full_path = workspace_root .. "/" .. M.config.activator_path

  -- Check if activator script exists
  if vim.fn.filereadable(activator_full_path) == 0 then
    vim.notify("Serena v2 auto-activator not found: " .. activator_full_path, vim.log.levels.WARN)
    return
  end

  -- Start in background
  local cmd = string.format("python %s > %s 2>&1 &", activator_full_path, M.config.log_file)
  vim.fn.system(cmd)

  vim.notify("Serena v2 auto-activator started", vim.log.levels.INFO)
end

-- Auto-start on VimEnter
if M.config.auto_start then
  vim.api.nvim_create_autocmd("VimEnter", {
    pattern = "*",
    callback = function()
      -- Delay slightly to let workspace detection settle
      vim.defer_fn(function()
        M.start()
      end, 100)
    end,
    desc = "Auto-start Serena v2"
  })
end

return M
