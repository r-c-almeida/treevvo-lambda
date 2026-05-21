# treevvo-lambda

Serviço de **geração de roteiros de viagem** com LLM (OpenAI), empacotado para rodar na **AWS Lambda** com trigger **SQS**.

## O que ele faz

1. **Entrada:** mensagens na fila SQS cujo corpo é um JSON com os mesmos campos da geração assíncrona (`user`, `folder`, `city`, `date_start`, `date_end`, `complementary_info`). O handler está em `lambda_function.py` → `lambda_handler`.

2. **Processamento:** para cada mensagem, o worker (`source/sqs_generate_worker.py`) valida o payload, instancia `GenerateScriptService`, que:
   - resolve a pasta de transcrições em relação à raiz configurada (`TRANSCRIPTS_ROOT` ou pasta do pacote no Lambda);
   - lê arquivos locais `transcricao*.txt` **se existirem** (se não houver, o pipeline segue sem transcrições);
   - executa `Application` → `RouterService`, orquestrando vários agentes (atrações, hotéis, dicas, roteirização, mapas, etc.) usando as instruções em `docs/instructions/*.txt` e o cliente em `source/llms/chatgpt_chat.py`.

3. **Saída:** o texto final do roteiro fica **em memória** (não grava arquivos `.txt` locais). Se `S3_TRIP_PROFILE_BUCKET` estiver definido, o resultado pode ser persistido no **S3** via `TripProfileS3Service` (perfil e viagens).

4. **Erros:** falhas por mensagem são registradas nos **logs** (ex.: CloudWatch). Em triggers com **Report batch item failures**, retornos com `batchItemFailures` permitem retry só das mensagens que falharam.

5. **Variáveis de ambiente:** exemplos e comentários em `.env.example` (OpenAI, SQS, S3, região, etc.).

## Deploy na AWS Lambda

- **Handler:** `lambda_function.lambda_handler`
- **Trigger:** fila SQS; recomenda-se habilitar **Report batch item failures** no mapeamento da fila.
- **Runtime:** alinhe a versão de Python da função com a do pacote gerado (por padrão o script usa wheels para **Python 3.14** em **x86_64**).

## Geração do pacote de deploy (ZIP)

Na **raiz do repositório**, com rede para o `pip` baixar dependências:

```bash
python scripts/build_lambda_zip.py
```

O artefato fica em **`dist/treevvo-lambda.zip`** (pasta `dist/` está no `.gitignore`).

### Variantes úteis

- Lambda **Graviton (ARM64):**

  ```bash
  python scripts/build_lambda_zip.py --platform manylinux2014_aarch64
  ```

- Runtime **Python 3.12** na AWS (em vez de 3.14):

  ```bash
  python scripts/build_lambda_zip.py --python-version 312
  ```

O script instala `requirements.txt` com wheels **manylinux** compatíveis com Linux da Lambda e copia `lambda_function.py`, `application.py`, `source/` e `docs/`.

## Testes locais (opcional)

- Consumir a **fila SQS real** com as mesmas credenciais da conta:

  ```bash
  python scripts/poll_sqs_local.py
  ```

- Invocar o handler com um evento de exemplo (arquivo em `events/sample-sqs-event.json`):

  ```bash
  python scripts/run_lambda_sample_event.py
  ```

## Dependências de runtime

Definidas em `requirements.txt`: `openai`, `python-dotenv`, `boto3` (e dependências transitivas no ZIP de deploy).
