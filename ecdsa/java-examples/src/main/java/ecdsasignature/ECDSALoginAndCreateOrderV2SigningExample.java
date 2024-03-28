package com.bullish.exchange.samples;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.bouncycastle.jce.provider.BouncyCastleProvider;
import org.bouncycastle.util.encoders.Base64;

import java.io.IOException;
import java.math.BigInteger;
import java.net.HttpURLConnection;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.security.*;
import java.security.spec.InvalidKeySpecException;
import java.security.spec.PKCS8EncodedKeySpec;
import java.time.Instant;
import java.time.temporal.ChronoUnit;

public class ECDSALoginAndCreateOrderV2SigningExample {

    private static final String BULLISH_HOST_NAME = "https://api.exchange.bullish.com";

    /// ECDSA API Keys - Replace with your trading keys and metadata /////
    private static final String PUBLIC_KEY_IN_PEM_FORMAT = """
                -----BEGIN PUBLIC KEY-----
                MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE3on42czkgbLfobhZnHOw2cvRLPw+
                ouotZAdvUO+BOc0yN9OS5aTplV2By9LT1+SuETeG4zLg7DytS4ct21ZZkA==
                -----END PUBLIC KEY-----
                """;

    private static final String PRIVATE_KEY_IN_PEM_FORMAT = """
                -----BEGIN PRIVATE KEY-----
                MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQgoE/ut6zgIQ2WBenX
                scngA998+4fOr9ISC8DCrHqH342hRANCAATeifjZzOSBst+huFmcc7DZy9Es/D6i
                6i1kB29Q74E5zTI305LlpOmVXYHL0tPX5K4RN4bjMuDsPK1Lhy3bVlmQ
                -----END PRIVATE KEY-----
                """;

    private static final String API_METADATA = """
                eyJhY2NvdW50SWQiOjIyMjAwMDAwMDAwMTYyNSwicHVibGljS2V5IjoiUFVCX1IxXzZlUEFUQlNIbmZvdDR4eEFHY1I0WTlmeXRMM01aNHFuSzNkQXNzcGtjUThUd0F4VHhBIiwiY3JlZGVudGlhbElkIjoiNjIwMSJ9
                """;

    /// Setup signing algorithms /////
    static {
        // To provide Signature algorithms like SHA256withECDSA
        Security.addProvider(new BouncyCastleProvider());
    }

    private static final String SHA256withECDSA = "SHA256withECDSA";

    public static void main(String[] args) throws IOException, NoSuchAlgorithmException, InvalidKeySpecException, SignatureException, NoSuchProviderException, InvalidKeyException, InterruptedException {
        final ObjectMapper objectMapper = new ObjectMapper()
                .configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);

        // Login to get the JWT token
        final LoginResponse loginResponse = login(objectMapper);
        final String tradingAccountId = fetchFirstTradingAccountId(loginResponse.getToken(), objectMapper);

        System.out.println("Using tradingAccountId: " + tradingAccountId);

        // Construct and sign the Create Order Request
        final BigInteger epochMilli = BigInteger.valueOf(Instant.now().toEpochMilli());
        final BigInteger nextNonce = BigInteger.valueOf(Instant.now().toEpochMilli()).multiply(BigInteger.valueOf(1000));

        final String createOrderUrlPath = "/trading-api/v2/orders";

        final CreateOrderRequest createOrderRequest = CreateOrderRequest.builder()
                .symbol("BTCUSDC")
                .commandType("V3CreateOrder")
                .type("LIMIT")
                .side("BUY")
                .price("1.5000") // Demo only. This is not likely to fill
                .quantity("1.0")
                .timeInForce("GTC")
                .clientOrderId(nextNonce.toString())
                .tradingAccountId(tradingAccountId)
                .build();

        final String bodyString = objectMapper.writeValueAsString(createOrderRequest);

        // Construct the signing payload
        final String payLoadToSign = epochMilli.toString()
                + nextNonce.toString()
                + "POST"
                + createOrderUrlPath
                + bodyString;

        // Sign and encode the resultant bytes in BASE64
        Signature sig = Signature.getInstance(SHA256withECDSA, "BC");
        sig.initSign(privateKey());
        sig.update(payLoadToSign.getBytes(StandardCharsets.UTF_8));
        String signature_base64 = Base64.toBase64String(sig.sign());

        // Send signature along, in the request
        HttpClient client = HttpClient.newHttpClient();
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(BULLISH_HOST_NAME + createOrderUrlPath))
                .POST(HttpRequest.BodyPublishers.ofString(bodyString))
                .header("Content-type", "application/json")
                .header("Authorization", "Bearer " + loginResponse.getToken())
                .header("BX-SIGNATURE", signature_base64)
                .header("BX-TIMESTAMP", epochMilli.toString())
                .header("BX-NONCE", nextNonce.toString())
                .build();

        var response = client.send(request, HttpResponse.BodyHandlers.ofString());
        System.out.println("CreateOrder API response:");
        System.out.println(response.statusCode());
        System.out.println(response.body());
    }

    private static LoginResponse login(ObjectMapper objectMapper) throws IOException, NoSuchAlgorithmException, NoSuchProviderException, InvalidKeySpecException, InvalidKeyException, SignatureException, InterruptedException {
        // Get the userId from API Metadata
        final ObjectNode metaData = metadata(objectMapper);
        final String userId = metaData.get("userId").asText();
        final Instant timestamp = Instant.now();

        // Create and sign the login request
        final LoginRequest loginRequest = LoginRequest.builder()
                .userId(userId)
                .nonce(timestamp.getEpochSecond())
                .expirationTime((timestamp.plus(300, ChronoUnit.SECONDS)).getEpochSecond())
                .biometricsUsed(false)
                .build();

        final String payloadToSign = objectMapper.writeValueAsString(loginRequest);

        final Signature sig = Signature.getInstance(SHA256withECDSA, "BC");
        sig.initSign(privateKey());
        sig.update(payloadToSign.getBytes(StandardCharsets.UTF_8));

        final String signature_base64 = Base64.toBase64String(sig.sign());

        // Wrap the login request and signature
        final LoginPayload loginPayload = LoginPayload.builder()
                .publicKey(PUBLIC_KEY_IN_PEM_FORMAT.trim())
                .signature(signature_base64)
                .loginPayload(loginRequest)
                .build();

        final String payloadToSend = objectMapper.writeValueAsString(loginPayload);

        // Do the login
        final HttpClient client = HttpClient.newHttpClient();
        final HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(BULLISH_HOST_NAME + "/trading-api/v2/users/login"))
                .POST(HttpRequest.BodyPublishers.ofString(payloadToSend))
                .header("Content-type", "application/json")
                .header("BX-SIGNATURE", signature_base64)
                .build();
        System.out.println("Getting JWT token");
        final var response = client.send(request, HttpResponse.BodyHandlers.ofString());

        if (response.statusCode() != HttpURLConnection.HTTP_OK) {
            System.err.println();
            throw new RuntimeException("Unable to login");
        }
        System.out.println("Getting JWT token [Success]");
        return objectMapper.readValue(response.body(), LoginResponse.class);
    }

    public static String fetchFirstTradingAccountId(String jwtToken, ObjectMapper objectMapper) throws IOException, InterruptedException {
        final HttpClient client = HttpClient.newHttpClient();
        final HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(BULLISH_HOST_NAME + "/trading-api/v1/accounts/trading-accounts"))
                .header("Content-type", "application/json")
                .header("Authorization", "Bearer " + jwtToken)
                .GET()
                .build();
        var response  = client.send(request, HttpResponse.BodyHandlers.ofString());

        if (response.statusCode() != HttpURLConnection.HTTP_OK) {
            throw new RuntimeException("Unable to fetch accounts");
        }

        final Account[] accounts = objectMapper.readValue(response.body(), Account[].class);
        if (accounts != null && accounts.length > 0) {
            return accounts[0].tradingAccountId;
        }

        throw new RuntimeException("No trading accounts to fetch");
    }

    private static PrivateKey privateKey() throws NoSuchAlgorithmException, InvalidKeySpecException {
        final String privateKeyContent = PRIVATE_KEY_IN_PEM_FORMAT
                .replace("-----BEGIN PRIVATE KEY-----", "")
                .replaceAll(System.lineSeparator(), "")
                .replace("-----END PRIVATE KEY-----", "");
        final byte[] encoded = Base64.decode(privateKeyContent);
        final KeyFactory keyFactory = KeyFactory.getInstance("EC");
        final PKCS8EncodedKeySpec keySpec = new PKCS8EncodedKeySpec(encoded);
        return keyFactory.generatePrivate(keySpec);
    }

    private static ObjectNode metadata(ObjectMapper objectMapper) throws IOException {
        return (ObjectNode) objectMapper.readTree(Base64.decode(API_METADATA));
    }

    ////// BOILER PLATE ////////

    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Data
    private static class LoginRequest {
        private String userId;
        private Long nonce;
        private Long expirationTime;
        private Boolean biometricsUsed;
        private String sessionKey;
    }

    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Data
    private static class LoginPayload {
        private String publicKey;
        private String signature;
        private LoginRequest loginPayload;
    }

    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Data
    private static class LoginResponse {
        private String authorizer;
        private String ownerAuthorizer;
        private String token;
    }

    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Data
    private static class Account {
        private String tradingAccountId;
    }

    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Data
    @JsonInclude(JsonInclude.Include.NON_NULL)
    private static class CreateOrderRequest {
        private String symbol;
        private String commandType;
        private String type;
        private String side;
        private String price;
        private String quantity;
        private String timeInForce;
        private String clientOrderId;
        private String tradingAccountId;
    }
}
