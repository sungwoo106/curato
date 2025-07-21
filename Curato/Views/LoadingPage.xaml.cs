using System;
using System.Threading.Tasks;
using System.Windows.Controls;
using System.Windows.Threading;
using System.Windows;

namespace Curato.Views
{
    public partial class LoadingPage : UserControl
    {
        private readonly DispatcherTimer dotTimer;
        private readonly DispatcherTimer progressTimer;
        private int dotCount = 0;
        private readonly string baseText = "Planning your trip";
        private double progress = 0;

        public LoadingPage()
        {
            InitializeComponent();
            Loaded += LoadingPage_Loaded;

            // Setup dot animation timer
            dotTimer = new DispatcherTimer
            {
                Interval = TimeSpan.FromMilliseconds(500)
            };
            dotTimer.Tick += DotTimer_Tick;
            
            // Fake loading progress bar timer
            progressTimer = new DispatcherTimer
            {
                Interval = TimeSpan.FromMilliseconds(30)
            };
            progressTimer.Tick += ProgressTimer_Tick;
        }

        private void DotTimer_Tick(object sender, EventArgs e)
        {
            dotCount = (dotCount + 1) % 4;
            LoadingTextBlock.Text = baseText + new string('.', dotCount);
        }

        private void ProgressTimer_Tick(object sender, EventArgs e)
        {
            progress += 2;
            ProgressBarFill.Width = progress * 3; // Max 300 width

            if (progress >= 100)
            {
                dotTimer.Stop();
                progressTimer.Stop();

                // Display the output page without using navigation
                var parentWindow = Window.GetWindow(this) as MainWindow;
                if (parentWindow != null)
                {
                    parentWindow.MainFrame.Content = new OutputPage();
                }
            }
        }

        private void LoadingPage_Loaded(object sender, RoutedEventArgs e)
        {
            dotTimer.Start();
            progressTimer.Start();
        }
    }
}
