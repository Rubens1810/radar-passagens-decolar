if (Test-Path build) { Remove-Item -Recurse -Force build }
New-Item -ItemType Directory -Path build/package | Out-Null

pip install httpx==0.27.2 python-dotenv==1.0.1 --platform manylinux2014_x86_64 --only-binary=:all: --target build/package

Copy-Item -Recurse src build/package/src

Compress-Archive -Path build/package/* -DestinationPath build/lambda_package.zip -Force
Write-Host "Pacote atualizado gerado em build/lambda_package.zip"
