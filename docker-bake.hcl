variable "MD2CONFLUENCE_VERSION" {
  default = "latest"
}

target "default" {
  context = "."
  args    = {
    MD2CONFLUENCE_VERSION = "${MD2CONFLUENCE_VERSION}"
  }
  tags = [
    "samobo/md2confluence:${MD2CONFLUENCE_VERSION}",
    "samobo/md2confluence:latest"
  ]
}