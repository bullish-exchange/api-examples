package ecdsawithdrawal;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.NoArgsConstructor;
import lombok.SneakyThrows;
import org.bouncycastle.jce.provider.BouncyCastleProvider;
import org.bouncycastle.util.encoders.Base64;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.security.*;
import java.security.spec.PKCS8EncodedKeySpec;
import java.time.Instant;
import java.util.UUID;

public class EcdsaWithdrawalExample {
    static {
        Security.addProvider(new BouncyCastleProvider());
    }

    private static final String BASE_URL = "https://api.exchange.bullish.com";
    private static final String LOGIN_ENDPOINT = "/trading-api/v2/users/login";
    private static final String WITHDRAWAL_INSTRUCTION_ENDPOINT = "/trading-api/v1/wallets/withdrawal-instructions/crypto/%s";
    private static final String WITHDRAW_ENDPOINT = "/trading-api/v1/wallets/withdrawal";

    public static void main(String[] args) {
        try {
            var objectMapper = new ObjectMapper();
            HttpClient client = HttpClient.newHttpClient();

            // Please replace it with your ecdsa api key metadata
            String metadata = "eyJ1c2VySWQdfgdOiIyMjIwMTk0MDQwNDgyMTQiLCJwdWJsaWNLZXkiOiItLS0tLUJFR0lOIFBVQkxJQyBLRVktLS0tLVxfhdjhfrd0V3WUhLb1pJemowQ0FRWUlLb1pJemowREFRY0RRZ0FFSStnQUhOL3FPQXVydjRtUjdJZVlpNzlCVloySFxubWRvZXhSaG1NZCsrVkZuZWR5RFZJT1NacUlycitEK3RjbU5GYzdqOW1XNVdWVfhdfMmZUcW54MXUrZz09XG4tLS0tLUVORCBQVUJMSUMgS0VZLS0tLS0iLCJjcmVkZW50aWFsSWQiOiIxyz";
            var ecdsaPrivateKeyInPem = // Please replace it with your ecdsa custody private key
                    """
                    -----BEGIN PRIVATE KEY-----
                    MIGHAgEAMBMGByqGSK49AgEGCCqGSM49AwEHBG0wcwIBAQQg+EQFH1xnWwT8VYmG
                    AYzO7osPAIcWdiuxgbgy0lWxLcSIGhRANCAAQj6AAc2+o4C6u/iZHsh4iLv0FVnYeZ
                    2h1FGGYx375UWd53INUg5Jnoiuv4P61yY0VzuP2ZblZVYvnZ9OqfHW77
                    -----END PRIVATE KEY-----
                    """;
            var wdlCoinSymbol = "EOS"; // coin you would like to withdraw
            var wdlNetwork = "EOS"; // network you would like to withdraw at

            // extract user id and public key
            String decodedMetadata = new String(Base64.decode(metadata));
            JsonNode decodedMetadataJson = objectMapper.readValue(decodedMetadata, JsonNode.class);
            String userId = decodedMetadataJson.get("userId").asText();
            String publicKey = decodedMetadataJson.get("publicKey").asText();

            // Read private key
            var privateKey = getPrivateKeyFromPem(ecdsaPrivateKeyInPem);

            // Fetch jwt token
            System.out.println("Fetching jwt token:");
            String jwtToken;
            long loginNonce =  Instant.now().toEpochMilli() / 1000;
            LoginPayload loginPayload = LoginPayload.builder()
                    .nonce(loginNonce)
                    .expirationTime(loginNonce + 300)
                    .userId(userId)
                    .sessionKey(null)
                    .biometricsUsed(false)
                    .build();
            var loginPayloadStr = objectMapper.writeValueAsString(loginPayload);
            var loginSignature = createSignature(loginPayloadStr, privateKey);

            var loginRequest = LoginRequest.builder()
                    .loginPayload(loginPayload)
                    .publicKey(publicKey)
                    .signature(loginSignature)
                    .build();

            var loginHttpRequest = HttpRequest.newBuilder(URI.create(BASE_URL + LOGIN_ENDPOINT))
                    .POST(HttpRequest.BodyPublishers.ofString(objectMapper.writeValueAsString(loginRequest)))
                    .header("Content-type", "application/json")
                    .build();
            var loginResponse  = client.send(loginHttpRequest, HttpResponse.BodyHandlers.ofString());
            System.out.printf("login response code: %s\n", loginResponse.statusCode());
            System.out.printf("login response: %s\n", loginResponse.body());

            var loginResponseBodyJson = objectMapper.readValue(loginResponse.body(), JsonNode.class);
            jwtToken = loginResponseBodyJson.get("token").asText();

            // Fetch withdraw instructions
            System.out.printf("Fetching %s withdrawal instructions:\n", wdlNetwork);
            HttpRequest withdrawInstructionHttpRequest = HttpRequest.newBuilder()
                    .uri(URI.create(BASE_URL + String.format(WITHDRAWAL_INSTRUCTION_ENDPOINT, wdlNetwork)))
                    .GET()
                    .header("Content-type", "application/json")
                    .header("Authorization", "Bearer " + jwtToken)
                    .build();

            var withdrawInstructionResponse = client.send(withdrawInstructionHttpRequest, HttpResponse.BodyHandlers.ofString());
            System.out.printf("withdraw instruction response code: %s\n", withdrawInstructionResponse.statusCode());
            System.out.printf("withdraw instruction response: %s\n",withdrawInstructionResponse.body());

            var wdlInstructionIterator = objectMapper.readTree(withdrawInstructionResponse.body()).iterator();

            if (!wdlInstructionIterator.hasNext()) {
                System.out.println("No whitelisted destination is found. No withdrawal could be made.");
                return;
            }

            var wdlDestinationId = wdlInstructionIterator.next().get("destinationId").asText();
            var withdrawTimestamp = String.valueOf(Instant.now().toEpochMilli());
            var withdrawNonce = UUID.randomUUID().toString();
            var withdrawRequest = CustodyApiWithdrawalRequest.builder()
                    .timestamp(withdrawTimestamp)
                    .nonce(withdrawNonce)
                    .authorizer("authorizer")
                    .command(CustodyApiWithdrawalCommand.builder()
                            .commandType("V1Withdrawal")
                            .destinationId(wdlDestinationId) // replace with your own destination id
                            .network(wdlNetwork)
                            .symbol(wdlCoinSymbol)
                            .quantity("1.01")
                            .build())
                    .build();

            // Create withdrawal signature
            var withdrawalRequestBodyStr = objectMapper.writeValueAsString(withdrawRequest);
            String withdrawalSignature = createSignature(withdrawTimestamp, withdrawNonce, "POST", WITHDRAW_ENDPOINT, withdrawalRequestBodyStr, privateKey);

            // Submit withdrawal
            System.out.printf("Creating %s withdrawal:\n", wdlCoinSymbol);
            HttpRequest withdrawHttpRequest = HttpRequest.newBuilder()
                    .uri(URI.create(BASE_URL + WITHDRAW_ENDPOINT))
                    .POST(HttpRequest.BodyPublishers.ofString(withdrawalRequestBodyStr))
                    .header("Content-type", "application/json")
                    .header("Authorization", "Bearer " + jwtToken)
                    .header("BX-SIGNATURE", withdrawalSignature)
                    .build();
            var withdrawResponse  = client.send(withdrawHttpRequest, HttpResponse.BodyHandlers.ofString());
            System.out.printf("withdraw response code: %s\n", withdrawResponse.statusCode());
            System.out.printf("withdraw response: %s\n", withdrawResponse.body());
        } catch (Exception e) {
            throw new RuntimeException("Unable to create an ecdsa withdrawal");
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

    @SneakyThrows
    public static String createSignature(String timestamp, String nonce, String httpMethod, String endpoint, String requestBodyStr, PrivateKey privateKey) {
        var payloadToSign =
                buildPreSignMessage(timestamp, nonce, httpMethod, endpoint, requestBodyStr);
        return createSignature(payloadToSign, privateKey);
    }

    @SneakyThrows
    public static String createSignature(String payloadString, PrivateKey privateKey) {
        Signature sig = Signature.getInstance("SHA256withECDSA", "BC");
        sig.initSign(privateKey);
        sig.update(payloadString.getBytes(StandardCharsets.UTF_8));
        return Base64.toBase64String(sig.sign());
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
        EcdsaWithdrawalExample.CustodyApiWithdrawalCommand command;
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

    @AllArgsConstructor
    @NoArgsConstructor
    @Builder
    @JsonInclude
    private static class LoginRequest {
        @JsonProperty("signature")
        private String signature;

        @JsonProperty("publicKey")
        private String publicKey;

        @JsonProperty("loginPayload")
        private LoginPayload loginPayload;
    }

    @AllArgsConstructor
    @NoArgsConstructor
    @Builder
    @JsonInclude
    private static class LoginPayload {
        @JsonProperty("userId")
        private String userId;

        @JsonProperty("nonce")
        private long nonce;

        @JsonProperty("expirationTime")
        private long expirationTime;

        @JsonProperty("biometricsUsed")
        private boolean biometricsUsed;

        @JsonProperty("sessionKey")
        private String sessionKey;
    }
}