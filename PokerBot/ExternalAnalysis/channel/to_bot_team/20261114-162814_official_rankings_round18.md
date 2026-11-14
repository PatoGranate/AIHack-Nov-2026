# Official Saturday rankings — round 18 snapshot

I fetched the public leaderboard directly from the endpoint used by the tournament PokerBots page at 16:26 UTC. The site reported 43 teams, round 18/54, and a 12-round ranking threshold. Source page: https://imperialaihack.com/pokerbots . Its client script `pokerbots.js?v=11` identifies the public data feed as `https://poker.imperialaihack.com/pokerbots/api/public`.

Top 10 (bb/100; latest site version; rounds/hands):
1. Gherkers +53.62, v19, 18/18,000
2. Attention Is All In +42.79, v3, 18/18,000
3. Kojack +36.36, v3, 18/18,000
4. Resonance Qt +35.80, v7, 18/18,000
5. Equity Engine +35.36, v9, 18/18,000
6. Phil AIvey +34.81, v6, 18/18,000
7. AAST +32.89, v4, 18/18,000
8. Anker Batteries +28.93, v3, 17/17,000
9. WBot +27.66, v5, 18/18,000
10. The Market Makers +26.42, v8, 18/18,000

WBot is 9th, still on v5 = G/v7. The public row says +99,591 chips, 28 timeouts, no errors or bank-outs. Local r001–r018 reconciles exactly to +99,591 chips; r016 +91.865, r017 -59.645, r018 +6.815 bb/100. The full snapshot and interpretation are saved in `ExternalAnalysis/Live_Leaderboard_Round18_20261114.txt`.

Please record these versions for opponent tracking and use the ranking to choose targets for held-out checks; do not infer a head-to-head edge from leaderboard rank alone.
