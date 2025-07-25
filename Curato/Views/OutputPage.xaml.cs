using System.Windows;
using System.Windows.Controls;
using System.Windows.Documents;



namespace Curato.Views
{
    public partial class OutputPage : UserControl
    {
        public OutputPage()
        {
            InitializeComponent();
            this.DataContext = AppState.SharedTripPlan;

            var plan = AppState.SharedTripPlan;
            // Debugging output
            // This will show the emotional narrative in a message box for debugging purposes
            MessageBox.Show(plan?.EmotionalNarrative ?? "No emotional story loaded");

            if (plan != null && !string.IsNullOrWhiteSpace(plan.EmotionalNarrative))
            {
                EmotionalItineraryTextBlock.Inlines.Clear();
                foreach (var para in plan.EmotionalNarrative.Split(new[] { "\n", "\r\n" }, StringSplitOptions.RemoveEmptyEntries))
                {
                    EmotionalItineraryTextBlock.Inlines.Add(new Run(para.Trim()));
                    EmotionalItineraryTextBlock.Inlines.Add(new LineBreak());
                    EmotionalItineraryTextBlock.Inlines.Add(new LineBreak());
                }
            }
        }

        private void EditButton_Click(object sender, RoutedEventArgs e)
        {
            var mainWindow = Window.GetWindow(this) as MainWindow;
            if (mainWindow != null)
            {
                mainWindow.MainFrame.Content = new SearchPage();
            }
        }
    }
}


