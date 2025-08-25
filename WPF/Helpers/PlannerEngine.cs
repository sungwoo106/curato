using System.Diagnostics;
using System.Text.Json;
using System.IO;
using Curato.Models;
using Curato.Helpers;
using System.Text;

/// <summary>
/// Engine for generating trip plans by calling Python backend
/// </summary>
public static class PlannerEngine
{
    /// <summary>
    /// Generates a trip plan by calling the Python backend
    /// </summary>
    /// <param name="request">Trip request with user preferences</param>
    /// <param name="progress">Progress reporter for real-time updates</param>
    /// <returns>Generated trip plan with itinerary and places</returns>
    public static async Task<TripPlan> GenerateTripPlan(TripRequest request, IProgress<(int progress, string message)>? progress = null)
    {
        try
        {
            // Map TripRequest to the format expected by generate_plan.py
            var payload = new
            {
                companion_type = request.Companion ?? "tSolo",
                budget = request.Budget switch
                {
                    "$" => "low",
                    "$$" => "medium", 
                    "$$$" => "high",
                    _ => "low"
                },
                starting_time = request.StartTime switch
                {
                    "00:00" => 0, "01:00" => 1, "02:00" => 2, "03:00" => 3, "04:00" => 4, "05:00" => 5,
                    "06:00" => 6, "07:00" => 7, "08:00" => 8, "09:00" => 9, "10:00" => 10, "11:00" => 11,
                    "12:00" => 12, "13:00" => 13, "14:00" => 14, "15:00" => 15, "16:00" => 16, "17:00" => 17,
                    "18:00" => 18, "19:00" => 19, "20:00" => 20, "21:00" => 21, "22:00" => 22, "23:00" => 23,
                    _ => 12
                },
                location_query = string.IsNullOrWhiteSpace(request.Location) || request.Location == "Search Location" ? null : request.Location,
                categories = request.PreferredPlaceTypes ?? new List<string>()
            };

            string json = JsonSerializer.Serialize(payload, new JsonSerializerOptions 
            { 
                Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping 
            });
            
            var scriptPath = Path.Combine(AppContext.BaseDirectory, "generate_plan.py");
            
            var psi = new ProcessStartInfo
            {
                FileName = "python",
                Arguments = $"\"{scriptPath}\"",
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
                CreateNoWindow = true,
                WorkingDirectory = AppContext.BaseDirectory
            };
            psi.StandardOutputEncoding = Encoding.UTF8;

            // Set the INPUT_JSON environment variable
            psi.Environment["INPUT_JSON"] = json;

            using var process = Process.Start(psi)!;
            
            // Variables to store the final result
            string? finalItinerary = null;
            string? finalRoutePlan = null;
            bool hasCompleted = false;
            
            // Handle streaming output for progress updates
            process.OutputDataReceived += (sender, e) =>
            {
                if (string.IsNullOrEmpty(e.Data)) return;
                
                try
                {
                    // Try to parse as JSON progress update
                    var progressData = JsonSerializer.Deserialize<JsonElement>(e.Data, new JsonSerializerOptions 
                    { 
                        Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping 
                    });
                    
                    if (progressData.TryGetProperty("type", out var typeElement))
                    {
                        string type = typeElement.GetString() ?? "";
                        
                        if (type == "progress" && progressData.TryGetProperty("progress", out var progressElement))
                        {
                            int progressValue = progressElement.GetInt32();
                            string message = progressData.TryGetProperty("message", out var messageElement) 
                                ? messageElement.GetString() ?? "" 
                                : "";
                            
                            // Report progress
                            progress?.Report((progressValue, message));
                            // Removed duplicate logging - progress is already logged in SearchPage.xaml.cs
                        }
                                                 else if (type == "phi_completion")
                         {
                             // Phi model completed - we can show the output page now
                             if (progressData.TryGetProperty("route_plan", out var routePlanElement))
                             {
                                 finalRoutePlan = routePlanElement.GetString();
                                 
                                 // Report Phi completion with route plan data to show output page immediately
                                 // Send the route plan data separately to avoid corrupting the JSON
                                 progress?.Report((85, $"phi_completion|{finalRoutePlan}"));
                             }
                         }
                        else if (type == "streaming_token")
                        {
                            // Handle streaming tokens for real-time story display
                            if (progressData.TryGetProperty("token", out var tokenElement))
                            {
                                string token = tokenElement.GetString() ?? "";
                                bool isFinal = progressData.TryGetProperty("is_final", out var isFinalElement) 
                                    ? isFinalElement.GetBoolean() 
                                    : false;
                                
                                if (!isFinal && !string.IsNullOrEmpty(token))
                                {
                                    // Send streaming token for real-time display
                                    progress?.Report((90, $"streaming_token:{token}"));
                                }
                                else if (isFinal)
                                {
                                    // Streaming completed
                                    progress?.Report((95, "Story streaming completed"));
                                }
                            }
                        }
                        else if (type == "completion")
                        {
                            // Extract both route plan and itinerary
                            if (progressData.TryGetProperty("route_plan", out var routePlanElement))
                            {
                                finalRoutePlan = routePlanElement.GetString();
                                Logger.LogInfo($"Received route plan: {finalRoutePlan?.Substring(0, Math.Min(100, finalRoutePlan?.Length ?? 0))}...");
                            }
                            else
                            {
                                Logger.LogInfo("No route_plan property found in completion message");
                            }
                            
                            if (progressData.TryGetProperty("itinerary", out var itineraryElement))
                            {
                                finalItinerary = itineraryElement.GetString();
                                Logger.LogInfo($"Received itinerary: {finalItinerary?.Substring(0, Math.Min(100, finalItinerary?.Length ?? 0))}...");
                            }
                            else
                            {
                                Logger.LogInfo("No itinerary property found in completion message");
                            }
                            
                            hasCompleted = true;
                        }
                    }
                }
                catch (JsonException)
                {
                    // If it's not valid JSON, it might be regular output (for backward compatibility)
                    if (!hasCompleted)
                    {
                        finalItinerary = e.Data;
                        hasCompleted = true;
                        Logger.LogInfo($"Received non-JSON output: {e.Data}");
                    }
                }
            };
            
            // Start reading output asynchronously
            process.BeginOutputReadLine();
            
            // Read error output (for debugging)
            string error = await process.StandardError.ReadToEndAsync();
            
            // Wait for the process to complete
            await process.WaitForExitAsync();
            
            // Log stderr output for troubleshooting
            if (!string.IsNullOrEmpty(error))
            {
                Logger.LogInfo($"Python stderr output: {error}");
            }
            
            // Wait a bit for any pending output processing
            await Task.Delay(100);
            
            // If we didn't get a completion message, try to parse the final output
            if (string.IsNullOrEmpty(finalItinerary))
            {
                Logger.LogInfo("No completion message received, checking for fallback output");
                // For backward compatibility, try to parse the entire output as a simple JSON
                try
                {
                    // This handles the old format where the script just outputs {"itinerary": "..."}
                    var fallbackOutput = await process.StandardOutput.ReadToEndAsync();
                    if (!string.IsNullOrEmpty(fallbackOutput))
                    {
                        using var doc = JsonDocument.Parse(fallbackOutput);
                        if (doc.RootElement.TryGetProperty("itinerary", out var itineraryElement))
                        {
                            finalItinerary = itineraryElement.GetString();
                            Logger.LogInfo($"Parsed fallback output: {finalItinerary?.Substring(0, Math.Min(100, finalItinerary?.Length ?? 0))}...");
                        }
                    }
                }
                catch (Exception ex)
                {
                    Logger.LogError($"Failed to parse fallback output: {ex.Message}");
                }
            }
            
            // Create the final result
            if (!string.IsNullOrEmpty(finalItinerary))
            {
                var tripPlan = new TripPlan { EmotionalNarrative = finalItinerary };
                
                // Parse the route plan JSON to populate SuggestedPlaces
                if (!string.IsNullOrEmpty(finalRoutePlan))
                {
                    try
                    {
                        var routePlanData = JsonSerializer.Deserialize<List<PhiPlace>>(finalRoutePlan, new JsonSerializerOptions 
                        { 
                            Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping 
                        });
                        if (routePlanData != null)
                        {
                            tripPlan.SuggestedPlaces = routePlanData;
                        }
                    }
                    catch (Exception ex)
                    {
                        Logger.LogError($"Failed to parse route plan JSON: {ex.Message}");
                    }
                }
                

                return tripPlan;
            }
            else
            {
                Logger.LogError("No itinerary received from Python script");
                return new TripPlan { EmotionalNarrative = "Failed to generate itinerary - no output received" };
            }
        }
        catch (Exception ex)
        {
            Logger.LogError($"PlannerEngine.GenerateTripPlan failed: {ex.Message}", ex);
            return new TripPlan { EmotionalNarrative = $"Error generating trip plan: {ex.Message}" };
        }
    }
}
