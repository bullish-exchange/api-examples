package ecdsasignature;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.NoArgsConstructor;
import org.bouncycastle.jce.provider.BouncyCastleProvider;
import org.bouncycastle.util.encoders.Base64;
import org.bouncycastle.util.io.pem.PemObject;
import org.bouncycastle.util.io.pem.PemReader;

import java.io.StringReader;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.security.*;
import java.security.spec.PKCS8EncodedKeySpec;
import java.security.spec.X509EncodedKeySpec;
import java.time.Instant;
import java.util.UUID;

public class EcdsaWithdrawalSignatureExample {
    static {
        Security.addProvider(new BouncyCastleProvider());
    }

    public static void main(String[] args) {
        try {
            // Read private key
            var exampleEcdsaPrivateKeyInPem = // Please replace it with your ecdsa custody private key
                    """
                    -----BEGIN PRIVATE KEY-----
                    sdbsfdhjhfGgfjhgfdjhfdjfbdbvs7774dbFddhfgdhgf+sdhgshdhsd
                    dbfdbvfTwhqibsvcbbccCchhdd+o4C6u/iZHsh5iLv0FVnYsdfhjdf7777t34wg
                    dnfg57fyhu74yfghdF4u8fduhfy7hgr73yubdheytyghbye73u8yrugy3g
                    -----END PRIVATE KEY-----
                    """;
            var privateKey = getPrivateKeyFromPem(exampleEcdsaPrivateKeyInPem);

            var timestamp = String.valueOf(Instant.now().toEpochMilli());
            var nonce = UUID.randomUUID().toString();
            var withdrawRequest = CustodyApiWithdrawalRequest.builder()
                    .timestamp(timestamp)
                    .nonce(nonce)
                    .authorizer("authorizer")
                    .command(CustodyApiWithdrawalCommand.builder()
                            .commandType("V1Withdrawal")
                            .destinationId("paste-your-destination-id-here") // replace with your own destination id
                            .network("CBIT")
                            .symbol("USD")
                            .quantity("1.02")
                            .build())
                    .build();

            // Create Signature
            var objectMapper = new ObjectMapper();
            var requestBodyStr = objectMapper.writeValueAsString(withdrawRequest);
            var payloadToSign =
                    buildPreSignMessage(timestamp, nonce, "POST", "/trading-api/v1/wallets/withdrawal", requestBodyStr);
            Signature sig = Signature.getInstance("SHA256withECDSA", "BC");
            sig.initSign(privateKey);
            sig.update(payloadToSign.getBytes(StandardCharsets.UTF_8));
            String signature = Base64.toBase64String(sig.sign());

            String baseUrl = "https://api.exchange.bullish.com";
            String jwtToken = "paste-your-jwt-token-here";
            HttpClient client = HttpClient.newHttpClient();
            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(baseUrl + "/trading-api/v1/wallets/withdrawal"))
                    .POST(HttpRequest.BodyPublishers.ofString(requestBodyStr))
                    .header("Content-type", "application/json")
                    .header("Authorization", "Bearer " + jwtToken)
                    .header("BX-SIGNATURE", signature)
                    .build();
            var response  = client.send(request, HttpResponse.BodyHandlers.ofString());
            System.out.println(response.statusCode());
            System.out.println(response.body());
        } catch (Exception e) {
            throw new RuntimeException("Unable to create an ecdsa signature");
        }
    }

    public static String buildPreSignMessage(
            String timestamp, String nonce, String method, String endpoint, String body) {
        StringBuilder sb = new StringBuilder();
        sb.append(timestamp);
        sb.append(nonce);
        sb.append(method);
        sb.append(endpoint);
        sb.append(body);
        return sb.toString();
    }

    public static PrivateKey getPrivateKeyFromPem(String privateKeyInPem) {
        try {
            String parsedPrivateKeyInPem = privateKeyInPem
                    .replace("-----BEGIN PRIVATE KEY-----", "")
                    .replaceAll(System.lineSeparator(), "")
                    .replace("-----END PRIVATE KEY-----", "");
            byte[] encoded = Base64.decode(parsedPrivateKeyInPem);
            KeyFactory keyFactory = KeyFactory.getInstance("EC");
            PKCS8EncodedKeySpec keySpec = new PKCS8EncodedKeySpec(encoded);
            return keyFactory.generatePrivate(keySpec);
        } catch (Exception e) {
            throw new RuntimeException("Unable to import private key");
        }
    }

    public static boolean verifySignature(String publicKeyInPem, String message, String signature) {
        try {
            Signature sig = Signature.getInstance("SHA256withECDSA", "BC");
            PublicKey publicKey = getPublicKeyFromPem(publicKeyInPem);
            sig.initVerify(publicKey);
            sig.update(message.getBytes(StandardCharsets.UTF_8));
            return sig.verify(Base64.decode(signature));
        } catch (Exception ex) {
            throw new RuntimeException("Unable to verify signature");
        }
    }

    public static PublicKey getPublicKeyFromPem(String publicKeyInPem) {
        try {
            PemReader pemReader = new PemReader(new StringReader(publicKeyInPem));
            PemObject pemObject = pemReader.readPemObject();
            X509EncodedKeySpec keySpec = new X509EncodedKeySpec(pemObject.getContent());
            KeyFactory keyFactory = KeyFactory.getInstance("EC");
            return keyFactory.generatePublic(keySpec);
        } catch (Exception e) {
            throw new RuntimeException("Unable to import public key");
        }
    }

    @AllArgsConstructor
    @NoArgsConstructor
    @Builder
    @JsonInclude
    private static class CustodyApiWithdrawalRequest {
        @JsonProperty("nonce")
        private String nonce;

        @JsonProperty("timestamp")
        private String timestamp;

        @JsonProperty("authorizer")
        private String authorizer;

        @JsonProperty("command")
        EcdsaWithdrawalSignatureExample.CustodyApiWithdrawalCommand command;
    }

    @AllArgsConstructor
    @NoArgsConstructor
    @Builder
    @JsonInclude
    private static class CustodyApiWithdrawalCommand {
        @JsonProperty("commandType")
        private String commandType;

        @JsonProperty("destinationId")
        private String destinationId;

        @JsonProperty("symbol")
        private String symbol;

        @JsonProperty("network")
        private String network;

        @JsonProperty("quantity")
        private String quantity;
    }
}