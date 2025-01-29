variable "MD2CONFLUENCE_VERSION" {
  default = "0.0.0-rc0"
}

target "default" {
  context = "."
  args    = {
    MD2CONFLUENCE_VERSION = "${MD2CONFLUENCE_VERSION}"
  }
  tags = [
    "samobo/md2confluence:${MD2CONFLUENCE_VERSION}",
  ]
}

target "release" {
  context = "."
  args    = {
    MD2CONFLUENCE_VERSION = "${MD2CONFLUENCE_VERSION}"
  }
  tags = [
    "samobo/md2confluence:${MD2CONFLUENCE_VERSION}",
    "samobo/md2confluence:latest"
  ]
}