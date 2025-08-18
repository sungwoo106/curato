using System.Diagnostics;
using System.Text.Json;
using System.IO;
using Curato.Models;

public static class PlannerEngine
{
    public static async Task<TripPlan> GenerateTripPlan(TripRequest request)
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

            string json = JsonSerializer.Serialize(payload);
            
            // Log the payload being sent to Python
            Logger.LogInfo($"Sending payload to Python: {json}");
            
            var scriptPath = Path.Combine(AppContext.BaseDirectory, "generate_plan.py");
            
            // Log the resolved script path for troubleshooting
            Logger.LogInfo($"Resolved script path: {scriptPath}");
            Logger.LogInfo($"Script file exists: {File.Exists(scriptPath)}");
            Logger.LogInfo($"Working directory: {AppContext.BaseDirectory}");
            
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
            psi.StandardOutputEncoding = System.Text.Encoding.UTF8;

            // Set the INPUT_JSON environment variable
            psi.Environment["INPUT_JSON"] = json;
            
            // Log the environment variable
            Logger.LogInfo($"Set INPUT_JSON environment variable: {json}");

            using var process = Process.Start(psi)!;
            string result = await process.StandardOutput.ReadToEndAsync();
            string error = await process.StandardError.ReadToEndAsync();
            await process.WaitForExitAsync();

            // Log stderr output for troubleshooting
            if (!string.IsNullOrEmpty(error))
            {
                Logger.LogInfo($"Python stderr output: {error}");
            }
            
            // Log the stdout output
            Logger.LogInfo($"Python stdout output: {result}");

            try
            {
                using var doc = JsonDocument.Parse(result);
                string? itinerary = doc.RootElement.GetProperty("itinerary").GetString();
                var tripPlan = new TripPlan { EmotionalNarrative = itinerary ?? result };
                
                // Log the final result
                Logger.LogInfo($"Final TripPlan EmotionalNarrative: {tripPlan.EmotionalNarrative}");
                
                return tripPlan;
            }
            catch (Exception parseEx)
            {
                Logger.LogError($"Failed to parse Python output: {parseEx.Message}", parseEx);
                Logger.LogInfo($"Raw output: {result}");
                return new TripPlan { EmotionalNarrative = result };
            }
        }
        catch (Exception ex)
        {
            Logger.LogError($"PlannerEngine.GenerateTripPlan failed: {ex.Message}", ex);
            return new TripPlan();
        }
    }
}
