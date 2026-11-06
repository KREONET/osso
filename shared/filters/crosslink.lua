-- 사이트 사이 링크(책 ↔ 실습)를 상대 URL로 바꾼다.
--
-- 한 저장소에 Quarto 프로젝트가 여럿(book/, lab/) 있고, 빌드 결과는
-- _site/book/, _site/lab/ 처럼 나란히 놓인다. 원고에서는 같은 원고 트리에
-- 있는 것처럼 `../01-image.md#1-2-image-formats` 로 링크를 걸고,
-- 링크 대상이 이 프로젝트에 없으면 이웃 프로젝트에서 찾아 HTML 주소로 바꾼다.

local SIBLINGS = { "book", "lab" }

local function file_exists(p)
  local f = io.open(p, "r")
  if f then f:close() return true end
  return false
end

local function dirname(p)
  return p:match("^(.*)/[^/]*$") or "."
end

-- "a/b/../c/./d" → "a/c/d"
local function normalize(p)
  local parts = {}
  for seg in p:gmatch("[^/]+") do
    if seg == ".." then
      if #parts > 0 and parts[#parts] ~= ".." then table.remove(parts) else table.insert(parts, "..") end
    elseif seg ~= "." then
      table.insert(parts, seg)
    end
  end
  return table.concat(parts, "/")
end

local project_dir, this_site, input_rel

local function setup()
  if project_dir then return end
  project_dir = quarto.project.directory
  this_site = project_dir:match("([^/]+)$")
  local input = quarto.doc.input_file
  input_rel = input:sub(#project_dir + 2)
end

-- 명시적 지정: [들어가며](book:index.qmd#addresses), [지도](lab:map.qmd)
-- 이름이 같은 파일(index.qmd)이 두 프로젝트에 다 있을 때 쓴다. 경로는 그 프로젝트 루트 기준.
local function explicit(el, site, rest)
  local depth = select(2, input_rel:gsub("/", ""))
  local path, frag = rest:match("^([^#]*)(#?.*)$")
  local html = path:gsub("%.q?md$", ".html")
  if site == this_site then
    el.target = string.rep("../", depth) .. html .. frag
  else
    el.target = string.rep("../", depth + 1) .. site .. "/" .. html .. frag
  end
  return el
end

function Link(el)
  setup()
  local t = el.target
  local site, rest = t:match("^(%a+):(.+)$")
  if site == "book" or site == "lab" then return explicit(el, site, rest) end
  if t:match("^%a[%w+.-]*:") or t:match("^#") or t:match("^/") then return nil end
  local path, frag = t:match("^([^#]*)(#?.*)$")
  if path == "" or not (path:match("%.md$") or path:match("%.qmd$") or path:match("%.html$")) then return nil end
  local rel = normalize(dirname(input_rel) .. "/" .. path)
  local mdrel = rel:gsub("%.html$", ".qmd"):gsub("%.md$", ".qmd")
  if file_exists(project_dir .. "/" .. mdrel) or file_exists(project_dir .. "/" .. rel) then return nil end
  local root = dirname(project_dir)
  for _, site in ipairs(SIBLINGS) do
    if site ~= this_site and file_exists(root .. "/" .. site .. "/" .. mdrel) then
      local depth = select(2, input_rel:gsub("/", ""))
      local up = string.rep("../", depth + 1)
      el.target = up .. site .. "/" .. mdrel:gsub("%.qmd$", ".html") .. frag
      return el
    end
  end
  return nil
end
