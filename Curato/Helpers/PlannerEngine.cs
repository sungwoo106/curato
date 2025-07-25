using System.Diagnostics;
using System.Text.Json;
using Curato.Models;

public static class PlannerEngine
{
    public static async Task<TripPlan> GenerateTripPlan(TripRequest request)
    {
        try
        {
            string args = JsonSerializer.Serialize(request);
            var psi = new ProcessStartInfo
            {
                FileName = "python",
                Arguments = $"generate_plan.py \"{args.Replace("\"", "\\\"")}\"",
                RedirectStandardOutput = true,
                UseShellExecute = false,
                CreateNoWindow = true
            };

            using var process = Process.Start(psi);
            string result = await process.StandardOutput.ReadToEndAsync();
            await process.WaitForExitAsync();

            var plan = JsonSerializer.Deserialize<TripPlan>(result);
            return plan ?? new TripPlan();
        }
        catch (Exception ex)
        {
            Debug.WriteLine("Trip generation failed: " + ex.Message);
            return new TripPlan();
        }
    }
}
