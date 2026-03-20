# MARS API Example Requests

> Source: Bloomberg Developer Portal — `developer.bloomberg.com/pages/doc-wp/mars_api_examples`  
> Owner: Jack Zhou  
> Captured: 2026-03-19

---

## Table of Contents

1. [Basic Pricing Requests](#basic-pricing-requests)
   - [Securities Pricing](#securities-pricing)
   - [Portfolio Pricing](#portfolio-pricing)
   - [Bulk Portfolio Pricing](#bulk-portfolio-pricing)
2. [Pricing Workflows](#pricing-workflows)
   - [Immediate Response Workflow](#immediate-response-workflow)
   - [Delayed Response Workflow (Polling)](#delayed-response-workflow-polling)
3. [Pricing Parameters](#pricing-parameters)
4. [Scenario Pricing](#scenario-pricing)
   - [Scenario Management](#scenario-management)
5. [Key Rate Risk Pricing Requests](#key-rate-risk-pricing-requests)
   - [Securities KRR Pricing Request](#securities-krr-pricing-request)
   - [Portfolio KRR Pricing Request](#portfolio-krr-pricing-request)
   - [Mortgage KRR Pricing Request: Custom Tenors](#mortgage-krr-pricing-request-custom-tenors)
6. [Advanced Pricing Features](#advanced-pricing-features)
   - [Identifier Types](#identifier-types)
   - [Asset Type Filter](#asset-type-filter)
   - [Security-Level Overrides and Attributes](#security-level-overrides-and-attributes)
7. [Deal Session Management](#deal-session-management)
8. [Market Data Features](#market-data-features)
   - [Market Data Session Management](#market-data-session-management)
   - [BVAL Cash Snapshot](#bval-cash-snapshot)
   - [MARS Golden Copy Snapshot](#mars-golden-copy-snapshot)
9. [Pre-Trade and Structuring](#pre-trade-and-structuring)
   - [Simple Pre-Trade Structuring](#simple-pre-trade-structuring)
   - [Displaying Deal Structure](#displaying-deal-structure)
   - [Saving Deal Structure](#saving-deal-structure)

---

## Basic Pricing Requests

### Securities Pricing

Given a single security or collection of securities, a set of pricing parameters, and requested fields, MARS API prices the securities and calculates the requested fields.

**Endpoint:** `POST /marswebapi/v1/securitiesPricing`

```json
{
    "securitiesPricingRequest": {
        "pricingParameter": {
            "valuationDate": "2024-04-18+00:00",
            "requestedField": [
                "MktPx",
                "MktVal",
                "Notional"
            ]
        },
        "security": [
            {
                "identifier": {
                    "bloombergDealId": "IBM 2.85 05/15/2040 Corp"
                }
            }
        ]
    }
}
```

---

### Portfolio Pricing

If you have an existing PRTU or a trading system (TS for AIM and TOMS) Portfolio with Bloomberg, you can price the entire portfolio using a `portfolioPricingRequest`. Rather than explicitly specifying securities, you can provide the portfolio name and portfolio source. MARS API will fetch the contents of the portfolio.

Valid inputs for `portfolioSource`:
- `PORTFOLIO`
- `PORTFOLIO_GROUP`
- `AIM_ACCOUNT`
- `AIM_ACCOUNT_GROUP`
- `TOMS_BOOK`
- `BVAL_PORTFOLIO`

You can also provide an optional `portfolioDate` parameter which will instruct MARS API to take a snapshot of the portfolio holdings on that date.

**Endpoint:** `POST /marswebapi/v1/portfolioPricing`

```json
{
    "portfolioPricingRequest": {
        "pricingParameter": {
            "valuationDate": "2024-04-18+00:00",
            "requestedField": [
                "MktPx",
                "MktVal",
                "Notional"
            ]
        },
        "portfolioDescription": {
            "portfolioName": "MARS API Samples",
            "portfolioSource": "PORTFOLIO",
            "portfolioDate": "2024-04-12+00:00"
        }
    }
}
```

---

### Bulk Portfolio Pricing

Similar to the portfolio pricing request, you can price multiple portfolios in a single `bulkPortfolioPricingRequest`.

**Endpoint:** `POST /marswebapi/v1/portfolioPricing`

```json
{
    "bulkPortfolioPricingRequest": {
        "pricingParameter": {
            "valuationDate": "2024-04-18+00:00",
            "requestedField": [
                "MktPx",
                "MktVal",
                "Notional"
            ]
        },
        "portfolioSourceDescription": {
            "portfolioDate": "2024-04-12+00:00",
            "portfolioSourceDetails": [
                {
                    "portfolioName": "Test Port 1",
                    "portfolioSource": "PORTFOLIO"
                },
                {
                    "portfolioName": "Test Port 2",
                    "portfolioSource": "PORTFOLIO"
                }
            ]
        }
    }
}
```

---

## Pricing Workflows

### Immediate Response Workflow

In the immediate response workflow, a pricing request will receive a series of `PricingResultResponse` messages containing the pricing results. In addition, a `HeartbeatResponse` message will be sent periodically to signal that the request is still processing. The pricing and analytic results for each of the positions may be spread across multiple `PricingResultResponse` messages depending on the size of the request. Therefore, clients should extract and aggregate the data from all of the `PricingResultResponse` messages together to form the complete MARS API response.

```json
{
    "heartbeatResponse": {
        "requestId": "535ea098-4074-4c4e-ae4d-c667a18bb854"
    }
}
```

---

### Delayed Response Workflow (Polling)

Depending on the Service Level Agreement of your contract, you may be enabled for delayed response handling. In these cases, a pricing request will result in a `ResultNotReadyResponse`. The `resultRetrievalId` from the `ResultNotReadyResponse` can be provided as input to a subsequent `ResultRetrievalRequest`. If the results are not yet available, MARS API will respond with another `ResultNotReadyResponse`. When the results are ready, MARS API will respond with a series of `PricingResultResponse` messages.

**Endpoint:** `GET /marswebapi/v1/results/Pricing/{result_id}`

```json
{
    "resultRetrievalRequest": {
        "resultRetrievalId": "b523764c-faad-49a7-bb59-a3151dea86f2"
    }
}
```

---

## Pricing Parameters

The `pricingParameters` element of the request defines a series of input parameters to be used in the pricing request. This is a common schema element that can be used across `securitiesPricingRequest`, `portfolioPricingRequest`, and `bulkPortfolioPricingRequest`.

| Parameter | Required | Description |
|---|---|---|
| `valuationDate` | Yes | Date on which to price the portfolio |
| `requestedField` | Yes | Array of desired output fields |
| `marketDataDate` | No | Date on which to snap the market data used for pricing. Defaults to `valuationDate` if omitted |
| `dealSession` | No | See [Deal Session Management](#deal-session-management) |
| `marketDataSession` | No | See [Market Data Session Management](#market-data-session-management) |
| `cashflow` | No | Projected and historical cashflows for applicable securities |
| `portfolioCurrency` | No | Currency used to calculate statistics associated with portfolio currency (e.g. `MktValPortCcy`) |
| `settingsSetId` | No | `SET <GO>` settings to be applied to the request |

**Pricing Request with Pricing Parameters:**

```json
{
    "securitiesPricingRequest": {
        "pricingParameter": {
            "valuationDate": "2024-04-18+00:00",
            "dealSession": "1161955508679329429",
            "marketDataSession": "3802870230334287768",
            "requestedField": [
                "MktPx",
                "MktVal",
                "Notional"
            ],
            "settingsSetId": "F-9001-CO-200",
            "cashflow": {
                "type": "ALL",
                "startDate": "2024-04-15+00:00",
                "endDate": "2029-04-14+00:00"
            }
        },
        "security": [
            {
                "identifier": {
                    "bloombergDealId": "SLWTCEQJ Corp"
                }
            }
        ]
    }
}
```

---

## Scenario Pricing

Pricing requests can include directives to apply scenarios to shift the market data used in pricing requests. Scenario requests are initiated with the inclusion of a `scenarioParameter` section.

**`scenarioParameter` fields:**

| Field | Required | Description |
|---|---|---|
| `scenarioId` | Yes | Array of SHOC IDs of the scenario(s) to apply. Generated via `SHOC <GO>` on the terminal |
| `requestedField` | Yes | Array of fields to calculate after the scenario is applied (distinct from base pricing fields) |
| `scenarioDate` | No | Date on which to apply the scenario. Defaults to `valuationDate` if not provided |

```json
{
    "securitiesPricingRequest": {
        "pricingParameter": {
            "valuationDate": "2024-11-10+00:00",
            "requestedField": [
                "MktPx",
                "MktVal",
                "Notional"
            ]
        },
        "scenarioParameter": {
            "scenario": [
                {
                    "scenarioId": "19529"
                },
                {
                    "scenarioId": "1780"
                }
            ],
            "requestedField": [
                "MktVal",
                "Delta"
            ],
            "scenarioDate": "2019-11-10+00:00"
        },
        "security": [
            {
                "identifier": {
                    "bloombergDealId": "IBM US Equity"
                }
            },
            {
                "identifier": {
                    "bloombergDealId": "IBM 2.85 05/15/2040 Corp"
                }
            }
        ]
    }
}
```

---

### Scenario Management

Scenarios can be created, destroyed, and viewed programmatically via MARS API.

| Operation | Endpoint |
|---|---|
| Create | `POST /marswebapi/v1/scenarios` |
| Get | `GET /marswebapi/v1/scenarios/{scenario_id}` |
| Delete | `DELETE /marswebapi/v1/scenarios` |

**Create Scenario Request:**

```json
{
    "scenarioRequest": {
        "createScenarioRequest": {
            "scenario": {
                "header": {
                    "name": "Test Scenario",
                    "description": "Test scenario for MARS API workflow"
                },
                "content": {
                    "regularScenario": {
                        "equitySpotShift": [
                            {
                                "shiftWhat": "Currency=USD",
                                "shiftMode": {
                                    "percent": {}
                                },
                                "shiftValue": {
                                    "scalarShift": 10
                                }
                            }
                        ]
                    }
                }
            }
        }
    }
}
```

**Delete Scenario Request:**

```json
{
    "scenarioRequest": {
        "deleteScenarioRequest": {
            "scenarioId": "6755601616930603012"
        }
    }
}
```

---

## Key Rate Risk Pricing Requests

Key rate risk (KRR) with respect to interest rate curve can be calculated at the securities level or portfolio level. A key rate risk ID is required to specify the rate shock details.

> To obtain a key rate risk ID: go to `MARS <GO>` → Settings → User Settings → Key Rate Risk → Greek Definition ID. Save your configuration to generate a new Greek Definition ID.

| Operation | Endpoint |
|---|---|
| Securities KRR (submit) | `POST /marswebapi/v1/securitiesKrr` |
| Portfolio KRR (submit) | `POST /enterprise/mars/portfolioKrr` |
| Securities KRR (retrieve) | `GET /marswebapi/v1/securitiesKrr/{result_id}` |
| Portfolio KRR (retrieve) | `GET /enterprise/mars/portfolioKrr/{result_id}` |

---

### Securities KRR Pricing Request

```json
{
    "securitiesKrrRequest": {
        "pricingParameter": {
            "valuationDate": "2024-07-03+00:00",
            "marketDataDate": "2024-07-03+00:00",
            "requestedField": [
                "SecurityCustomID",
                "MktPx",
                "ValuationDate",
                "YTM",
                "YTW",
                "YieldtoNextCall",
                "WorkoutDate",
                "I-Spread",
                "G-Spread",
                "YASDuration",
                "YASConvexity",
                "YASModifiedDuration",
                "BenchmarkYield",
                "ModifiedDuration",
                "Convexity",
                "OAS",
                "Delta",
                "Gamma",
                "Vega",
                "Theta",
                "DV01",
                "Credit DV01",
                "SpreadDuration",
                "Notional",
                "Principal",
                "AccruedInterest",
                "MktVal"
            ]
        },
        "krrDefinition": {
            "id": "6566651493789990921",
            "externalName": "mars api per currency krr shift zero annual"
        },
        "security": [
            {
                "identifier": { "bloombergDealId": "SLLG1NLH Corp" },
                "position": 100,
                "customId": "57648755"
            },
            {
                "identifier": { "bloombergDealId": "SLLG1NLW Corp" },
                "position": 100,
                "customId": "57648757"
            },
            {
                "identifier": { "bloombergDealId": "SLLG1NMB Corp" },
                "position": 100,
                "customId": "57685999"
            },
            {
                "identifier": { "bloombergDealId": "SLLG1NMH Corp" },
                "position": 100,
                "customId": "57686001"
            }
        ]
    }
}
```

---

### Portfolio KRR Pricing Request

```json
{
    "pricingParameter": {
        "valuationDate": "2024-10-02+00:00",
        "requestedField": [
            "SecurityCustomID",
            "MktPx",
            "ValuationDate",
            "YTM",
            "YTW",
            "YieldtoNextCall",
            "WorkoutDate",
            "I-Spread",
            "G-Spread",
            "YASDuration",
            "YASConvexity",
            "YASModifiedDuration",
            "BenchmarkYield",
            "ModifiedDuration",
            "Convexity",
            "OAS",
            "Delta",
            "Gamma",
            "Vega",
            "Theta",
            "DV01",
            "Credit DV01",
            "SpreadDuration",
            "Notional",
            "Principal",
            "AccruedInterest",
            "MktVal"
        ]
    },
    "krrDefinition": {
        "id": "6566651493789990921",
        "externalName": "mars api per currency krr shift zero annual"
    },
    "portfolio": {
        "portfolioName": "MARS UPLOAD DEFAULT",
        "portfolioSource": "PORTFOLIO",
        "portfolioDate": "2024-10-02+00:00"
    }
}
```

---

### Mortgage KRR Pricing Request: Custom Tenors

Custom tenors are only supported for mortgage securities. The response contains both KRR and KRD for each tenor. Default `shiftSize` for mortgage KRD should be 5 bps.

```json
{
    "securitiesKrrRequest": {
        "pricingParameter": {
            "valuationDate": "2024-11-25+00:00",
            "requestedField": [
                "MktPx",
                "MktVal"
            ]
        },
        "krrDefinition": {
            "id": "Not used",
            "externalName": "Not used",
            "krrConfig": {
                "tenor": [
                    {
                        "term": 1,
                        "unit": "YEAR"
                    },
                    {
                        "term": 6,
                        "unit": "MONTH"
                    }
                ],
                "shiftSize": 11.22,
                "shiftMethod": "WAVE"
            }
        },
        "security": [
            {
                "identifier": {
                    "bloombergDealId": "!!01IBUX   Mtge"
                },
                "position": 1
            }
        ]
    }
}
```

---

## Advanced Pricing Features

### Identifier Types

MARS API supports multiple input security identifier types.

| Identifier Type | Description |
|---|---|
| `bloombergDealId` | Bloomberg parsekeyable identifier (e.g. `IBM US Equity`) |
| `bloombergUniqueId` | Bloomberg unique ID |
| `dealHandle` | Internal deal handle |
| `CUSIP` | CUSIP number |
| `ISIN` | ISIN number |
| `SEDOL` | SEDOL number |
| `FIGI` | FIGI identifier |

```json
{
    "securitiesPricingRequest": {
        "pricingParameter": {
            "valuationDate": "2024-04-18+00:00",
            "requestedField": [
                "MktPx",
                "MktVal",
                "Notional"
            ]
        },
        "security": [
            { "identifier": { "ISIN": "US02079K3059" } },
            { "identifier": { "SEDOL": "2000019" } },
            { "identifier": { "bloombergUniqueId": "EQ0010172900001000" } },
            { "identifier": { "bloombergDealId": "IBM US Equity" } },
            { "identifier": { "CUSIP": "459200KA" } },
            { "identifier": { "dealHandle": "3000JD6Z7DAHGH6ZNJ0K1TGF207C5" } }
        ]
    }
}
```

---

### Asset Type Filter

Only price deals in a portfolio that match provided, comma-separated, filters. Unmatched deals are filtered out and not priced.

> Values for the filter can be seen by loading `{FLDS DS213}` on the Bloomberg Terminal.

```json
{
    "portfolioPricingRequest": {
        "pricingParameter": {
            "valuationDate": "2024-08-14+00:00",
            "requestedField": [
                "MktPx",
                "MktVal",
                "Notional"
            ]
        },
        "portfolioDescription": {
            "portfolioName": "MARS API Samples",
            "portfolioSource": "PORTFOLIO",
            "portfolioDate": "2024-08-14+00:00",
            "additionalParameter": [
                {
                    "name": "AssetTypeFilter",
                    "value": {
                        "stringVal": "ADR,Common Stock,Dutch Cert,Equity Option,ETP,FORWARD"
                    }
                }
            ]
        }
    }
}
```

---

### Security-Level Overrides and Attributes

For security pricing requests, the following parameters can be overridden at the security level:

- **Settlement Date**
- **Position**
- **Market Price**
- **Market Data Overrides** (IR discount curve and IR volatility cube overrides)

```json
{
    "securitiesPricingRequest": {
        "pricingParameter": {
            "valuationDate": "2024-04-18+00:00",
            "requestedField": [
                "MktPx",
                "MktVal",
                "Notional"
            ]
        },
        "security": [
            {
                "identifier": {
                    "bloombergDealId": "SL1S4GQS Corp"
                },
                "marketDataOverrides": {
                    "interestRateCurveOverrides": [
                        {
                            "category": "DISCOUNT_CURVE",
                            "overrideCurveId": "S50",
                            "currency": "USD"
                        }
                    ],
                    "interestRateVolatilityCubeOverrides": [
                        {
                            "cubeName": "USD Flat Vol",
                            "currency": "USD"
                        }
                    ]
                }
            },
            {
                "identifier": {
                    "bloombergDealId": "FN888888 Mtge"
                },
                "position": 1,
                "settlementDate": "2024-02-02+00:00"
            },
            {
                "identifier": {
                    "bloombergDealId": "IBM 7 10/30/25 Corp"
                },
                "marketPrice": 90
            }
        ]
    }
}
```

---

## Deal Session Management

Deal sessions can be referenced in pricing requests and re-used for multiple requests.

> **Recommendation:** Open a single MARS deal session every day and close it at the end of the day. Internally, MARS uses the session ID for caching deal parameters to improve performance of pricing requests.

| Operation | Endpoint |
|---|---|
| Start Deal Session | `POST /marswebapi/v1/sessions` |
| Delete Deal Session | `DELETE /marswebapi/v1/sessions/{session_id}` |

**Start Deal Session Request:**

```json
{
    "startSession": {
        "showDealType": false
    }
}
```

---

## Market Data Features

### Market Data Session Management

When pricing securities, MARS will create a temporary market data session cache to use to evaluate securities and portfolios. Similar to Deal Sessions, MARS API clients can specify a Market Data Session ID to re-use the cache across multiple pricing requests. Market Data Sessions can be initialized with no data using an empty request body, or using an XMKT session as the input. Once created, the market data session ID can be provided in the `pricingParameters` section of the request.

**Initialize empty Market Data Session:**

```json
{
    "startMarketDataSessionRequest": {}
}
```

**Initialize Market Data Session from XMKT:**

```json
{
    "startMarketDataSessionRequest": {
        "marketId": "XA03168000FDSRVBTXMKT5DADC00C"
    }
}
```

---

### BVAL Cash Snapshot

Market data snapshots for consistent pricing of cash instruments only, provided as an argument to the pricing request.

**Supported `bvalCashSnapshot` values:**

| Market | Times Available |
|---|---|
| Tokyo | `TOKYO_3PM`, `TOKYO_4PM`, `TOKYO_5PM` |
| London | `LONDON_12PM`, `LONDON_3PM`, `LONDON_4PM` |
| New York | `NEWYORK_3PM`, `NEWYORK_4PM` |

```json
{
    "securitiesPricingRequest": {
        "pricingParameter": {
            "valuationDate": "2024-11-06-05:00",
            "requestedField": [
                "MktPx"
            ],
            "marketDataSnapshot": {
                "bvalCashSnapshot": "NEWYORK_4PM"
            }
        },
        "security": [
            {
                "identifier": {
                    "bloombergDealId": "EC7676553 Corp"
                }
            }
        ]
    }
}
```

---

### MARS Golden Copy Snapshot

An alternative to the BVAL Cash snapshot. While BVAL Cash is for cash instruments only, the Golden Copy Snapshot is a comprehensive market data snapshot for **both derivatives and cash instruments**.

> **Note:** Use of golden copy snapshots requires setting `useBbgRecommendedSettings` to `true`. This ensures that the settings used for pricing match those used to derive the snapshot.

```json
{
    "securitiesPricingRequest": {
        "pricingParameter": {
            "valuationDate": "2024-11-06-05:00",
            "requestedField": [
                "MktPx"
            ],
            "marketDataSnapshot": {
                "goldenCopy": "NEWYORK_4PM"
            },
            "useBbgRecommendedSettings": true
        },
        "security": [
            {
                "identifier": {
                    "bloombergDealId": "GOOG US Equity"
                }
            },
            {
                "identifier": {
                    "bloombergDealId": "!!01IBUZ Mtge"
                }
            }
        ]
    }
}
```

---

## Pre-Trade and Structuring

### Simple Pre-Trade Structuring

Create a hypothetical deal for pre-trade purposes. Use `structureRequest` and receive a list of deal terms as well as a temporary deal handle.

**Endpoint:** `POST /marswebapi/v1/deals/temporary`

```json
{
    "structureRequest": {
        "sessionId": "6551343697652875265",
        "tail": "IR.FXFL"
    }
}
```

---

### Displaying Deal Structure

The `structureRequest` can also be used to echo back the deal terms of a known existing deal or temporary deal handle.

**By deal handle:**

```json
{
    "structureRequest": {
        "sessionId": "6551343697652875265",
        "tail": "3000HZRL5X96X1M1MKZZBHJH4Z65F"
    }
}
```

**By Bloomberg Deal ID:**

```json
{
    "structureRequest": {
        "sessionId": "6551343697652875265",
        "tail": "SLFQ000Y"
    }
}
```

---

### Saving Deal Structure

To convert a hypothetical deal to a permanent deal, use the `saveRequest`.

**Endpoint:** `PATCH /marswebapi/v1/deals/temporary/{deal_id}`

```json
{
    "saveRequest": {
        "dealHandle": "3000HZRL5X96X1M1MKZZBHJH4Z65F"
    }
}
```

---

*© 2026 Bloomberg L.P. All rights reserved.*
