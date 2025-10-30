import type { ValidateMessages } from "rc-field-form/lib/interface"

export const APP_TITLE = import.meta.env.VITE_APP_TITLE // 页面标题

// Extract company from URL path (e.g., /ui/irmsdev2 -> irmsdev2)
const getCompanyFromPath = (): string | null => {
  const pathParts = window.location.pathname.split("/").filter((p) => p)
  // Check if URL matches /ui/{company} pattern
  // pathParts[0] should be 'ui', pathParts[1] should be the company
  if (pathParts.length >= 2 && pathParts[0] === "ui" && pathParts[1] && pathParts[1] !== "assets") {
    return pathParts[1]
  }
  return null
}

const company = getCompanyFromPath()
// If company exists, use company-specific API path
export const basePath = company ? `/api/${company}` : import.meta.env.VITE_APP_GATWAY || "/api"

// export const jumpUrl = import.meta.env.VITE_JUMP_URL || ""; // 跳转url

export const defaultSuccessTip = "操作成功"

export const validateMessages: ValidateMessages = {
  required: "该字段为必填"
}
